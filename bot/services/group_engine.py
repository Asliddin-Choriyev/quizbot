import asyncio
import logging
import time
import random
from pathlib import Path
from typing import Dict, Optional, Any, List
from aiogram import Bot
from aiogram.types import CallbackQuery, PollAnswer, FSInputFile

import config
from bot.database.db import Database
from bot.database import queries
from bot.database.models import GroupCompetition, Question
from bot.keyboards.inline import get_group_lobby_kb
from bot.utils.i18n import t
from bot.utils.formatters import escape_html, format_leaderboard

logger = logging.getLogger(__name__)

# Active group poll mapping: poll_id -> dict
_active_group_polls: Dict[str, Dict[str, Any]] = {}
# Active competition timers: comp_id -> asyncio.Task
_active_group_timers: Dict[int, asyncio.Task] = {}
# Active competition current poll mapping: comp_id -> (poll_id, message_id)
_active_comp_polls: Dict[int, tuple[str, int]] = {}
# Cached Telegram file IDs for images: image_path -> file_id
_cached_file_ids: Dict[str, str] = {}

def cancel_group_timer(comp_id: int):
    task = _active_group_timers.pop(comp_id, None)
    try:
        current = asyncio.current_task()
    except RuntimeError:
        current = None
    if task and task != current and not task.done():
        task.cancel()

class GroupQuizEngine:
    def __init__(self, bot: Bot, db: Database):
        self.bot = bot
        self.db = db

    async def open_lobby(self, chat_id: int, quiz_id: int, creator_id: int, lang: str = "uz") -> Optional[int]:
        """Create and post a group competition lobby."""
        async with self.db.get_connection() as conn:
            quiz = await queries.get_quiz(conn, quiz_id)
            if not quiz:
                return None

            question_ids = await queries.get_question_ids_by_quiz(conn, quiz_id)
            if not question_ids:
                return None

            active_comp = await queries.get_active_group_competition(conn, chat_id)
            if active_comp:
                cancel_group_timer(active_comp.id)
                await queries.update_group_competition(conn, active_comp.id, status="cancelled")

            comp_id = await queries.create_group_competition(
                conn,
                quiz_id=quiz_id,
                chat_id=chat_id,
                created_by=creator_id,
                total_questions=len(question_ids),
                timer_seconds=quiz.default_timer or 25,
                question_ids=question_ids
            )

        text = t(
            "group_lobby_title",
            lang,
            title=escape_html(quiz.title),
            description=escape_html(quiz.description or ""),
            question_count=len(question_ids),
            timer=quiz.default_timer or 25
        )
        kb = get_group_lobby_kb(comp_id, lang=lang)

        msg = await self.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=kb,
            parse_mode="HTML"
        )
        async with self.db.get_connection() as conn:
            await queries.update_group_competition(conn, comp_id, message_id=msg.message_id)

        return comp_id

    async def handle_join(self, callback: CallbackQuery, comp_id: int, lang: str = "uz"):
        """Register a user to join the group competition lobby."""
        user = callback.from_user
        async with self.db.get_connection() as conn:
            comp = await queries.get_group_competition(conn, comp_id)
            if not comp or comp.status != "lobby":
                await callback.answer("Musobaqa yakunlangan yoki faol emas.", show_alert=True)
                return

            full_name = f"{user.first_name} {user.last_name or ''}".strip()
            await queries.register_group_participant(
                conn,
                competition_id=comp_id,
                user_id=user.id,
                username=user.username,
                full_name=full_name
            )

        await callback.answer(t("joined_competition", lang), show_alert=False)

    async def start_competition(self, callback: CallbackQuery, comp_id: int, lang: str = "uz"):
        """Start the competition from the lobby."""
        async with self.db.get_connection() as conn:
            comp = await queries.get_group_competition(conn, comp_id)
            if not comp or comp.status != "lobby":
                return

            if callback.from_user.id != comp.created_by:
                try:
                    chat_member = await self.bot.get_chat_member(comp.chat_id, callback.from_user.id)
                    if chat_member.status not in ("creator", "administrator"):
                        await callback.answer(t("not_group_creator", lang), show_alert=True)
                        return
                except Exception:
                    pass

            await queries.update_group_competition(conn, comp_id, status="active", current_question_index=0)
            comp = await queries.get_group_competition(conn, comp_id)

        await callback.answer()
        await self.send_group_question(comp, lang=lang)

    async def send_group_question(self, comp: GroupCompetition, lang: str = "uz"):
        """Send question as a native Telegram Quiz Poll to the group."""
        cancel_group_timer(comp.id)

        if comp.current_question_index >= comp.total_questions:
            await self.finish_competition(comp, lang=lang)
            return

        question_id = comp.question_ids_order[comp.current_question_index]

        async with self.db.get_connection() as conn:
            quiz = await queries.get_quiz(conn, comp.quiz_id)
            question = await queries.get_question(conn, question_id)

        if not question or not quiz:
            await self.finish_competition(comp, lang=lang)
            return

        timer = question.timer_seconds or comp.timer_seconds or 25
        timer = max(5, min(600, timer))

        options = list(question.options)
        if quiz.shuffle_options:
            random.shuffle(options)

        correct_idx = next((i for i, opt in enumerate(options) if opt.is_correct), 0)

        curr_idx = comp.current_question_index + 1
        q_text = f"[{curr_idx}/{comp.total_questions}] {question.question_text}"
        if len(q_text) > 300:
            q_text = q_text[:297] + "..."

        opt_texts = [opt.option_text[:100] for opt in options]
        exp_text = (question.explanation or "")[:200] if quiz.show_explanation else None

        # Send question image if available
        if question.image_url:
            try:
                cached_id = _cached_file_ids.get(question.image_url)
                if cached_id:
                    await self.bot.send_photo(chat_id=comp.chat_id, photo=cached_id)
                else:
                    img_path = Path(question.image_url)
                    if not img_path.is_absolute():
                        img_path = config.BASE_DIR / img_path
                    if img_path.exists():
                        photo_msg = await self.bot.send_photo(chat_id=comp.chat_id, photo=FSInputFile(str(img_path)))
                        if photo_msg and photo_msg.photo:
                            _cached_file_ids[question.image_url] = photo_msg.photo[-1].file_id
                    elif question.image_url.startswith(("http://", "https://")):
                        photo_msg = await self.bot.send_photo(chat_id=comp.chat_id, photo=question.image_url)
                        if photo_msg and photo_msg.photo:
                            _cached_file_ids[question.image_url] = photo_msg.photo[-1].file_id
            except Exception as e:
                logger.warning(f"Error sending group question image: {e}")

        try:
            poll_msg = await self.bot.send_poll(
                chat_id=comp.chat_id,
                question=q_text,
                options=opt_texts,
                type="quiz",
                correct_option_id=correct_idx,
                explanation=exp_text,
                open_period=timer,
                is_anonymous=False
            )
        except Exception as e:
            logger.exception(f"Error sending group poll for comp {comp.id}: {e}")
            try:
                await self.bot.send_message(
                    chat_id=comp.chat_id,
                    text=f"⚠️ Savolni yuborishda xatolik yuz berdi ({e}). Keyingi savolga o'tilmoqda..."
                )
                await asyncio.sleep(2)
                async with self.db.get_connection() as conn:
                    new_idx = comp.current_question_index + 1
                    await queries.update_group_competition(conn, comp.id, current_question_index=new_idx)
                    updated_comp = await queries.get_group_competition(conn, comp.id)
                if updated_comp:
                    await self.send_group_question(updated_comp, lang=lang)
            except Exception as inner_e:
                logger.error(f"Error recovering from send_poll failure: {inner_e}")
            return

        poll_id = poll_msg.poll.id
        _active_comp_polls[comp.id] = (poll_id, poll_msg.message_id)
        _active_group_polls[poll_id] = {
            "comp_id": comp.id,
            "quiz_id": comp.quiz_id,
            "question_id": question.id,
            "correct_idx": correct_idx,
            "options": options,
            "start_time": time.time(),
            "timer": timer
        }

        # Schedule timer for group round end
        timer_task = asyncio.create_task(
            self._handle_group_round_timeout(comp.id, question.id, poll_id, timer, lang)
        )
        _active_group_timers[comp.id] = timer_task

    async def _handle_group_round_timeout(self, comp_id: int, question_id: int, poll_id: str, duration: int, lang: str):
        """Called when round time expires in group mode."""
        try:
            await asyncio.sleep(duration + 0.5)
        except asyncio.CancelledError:
            return

        _active_group_polls.pop(poll_id, None)

        async with self.db.get_connection() as conn:
            comp = await queries.get_group_competition(conn, comp_id)
            if not comp or comp.status != "active":
                return

            current_q_id = comp.question_ids_order[comp.current_question_index]
            if current_q_id != question_id:
                return

            participants = await queries.get_group_participants(conn, comp_id)

            # Advance index
            new_idx = comp.current_question_index + 1
            await queries.update_group_competition(conn, comp_id, current_question_index=new_idx)
            comp = await queries.get_group_competition(conn, comp_id)

        # Brief delay (2.0s) so participants can see the correct answer on the closed poll
        await asyncio.sleep(2.0)
        await self.send_group_question(comp, lang=lang)

    async def process_group_poll_answer(self, poll_answer: PollAnswer):
        """Process group poll answers from participants."""
        poll_id = poll_answer.poll_id
        poll_data = _active_group_polls.get(poll_id)
        if not poll_data or not poll_answer.option_ids:
            return

        user = poll_answer.user
        selected_idx = poll_answer.option_ids[0]
        is_correct = (selected_idx == poll_data["correct_idx"])
        selected_opt = poll_data["options"][selected_idx]

        response_time = round(time.time() - poll_data["start_time"], 2)
        points = 10 if is_correct else 0
        full_name = f"{user.first_name} {user.last_name or ''}".strip()

        async with self.db.get_connection() as conn:
            await queries.record_group_answer(
                conn,
                competition_id=poll_data["comp_id"],
                question_id=poll_data["question_id"],
                user_id=user.id,
                username=user.username,
                full_name=full_name,
                selected_option=selected_opt.option_label,
                is_correct=is_correct,
                response_time_seconds=response_time,
                points=points
            )

    async def finish_competition(self, comp: GroupCompetition, lang: str = "uz", was_cancelled: bool = False):
        """Post final group competition leaderboard."""
        cancel_group_timer(comp.id)
        _active_comp_polls.pop(comp.id, None)

        async with self.db.get_connection() as conn:
            status = "cancelled" if was_cancelled else "finished"
            await queries.update_group_competition(conn, comp.id, status=status)
            quiz = await queries.get_quiz(conn, comp.quiz_id)
            participants = await queries.get_group_participants(conn, comp.id)

        rankings = [
            {"full_name": p.full_name, "score": p.score, "correct_answers": p.correct_answers}
            for p in participants
        ]
        board_text = format_leaderboard(rankings, max_items=10)

        header = "🛑 <b>Test muddatidan oldin to'xtatildi!</b>\n\n" if was_cancelled else ""
        final_text = (
            f"{header}"
            + t(
                "group_final_leaderboard",
                lang,
                title=escape_html(quiz.title if quiz else "Quiz"),
                total=comp.total_questions,
                leaderboard=board_text
            )
        )

        try:
            await self.bot.send_message(chat_id=comp.chat_id, text=final_text, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Error posting final group leaderboard: {e}")

    async def stop_competition(self, chat_id: int, lang: str = "uz"):
        """Cancel the active competition in chat, close active poll, and show final results."""
        async with self.db.get_connection() as conn:
            comp = await queries.get_active_group_competition(conn, chat_id)
            if not comp:
                await self.bot.send_message(chat_id=chat_id, text="ℹ️ Guruhda faol musobaqa yo'q.")
                return

        cancel_group_timer(comp.id)

        # Stop active poll in Telegram if open
        poll_info = _active_comp_polls.pop(comp.id, None)
        if poll_info:
            poll_id, msg_id = poll_info
            _active_group_polls.pop(poll_id, None)
            try:
                await self.bot.stop_poll(chat_id=chat_id, message_id=msg_id)
            except Exception as e:
                logger.debug(f"Could not stop active poll: {e}")

        await self.finish_competition(comp, lang=lang, was_cancelled=True)

    async def process_group_answer(self, callback: CallbackQuery, comp_id: int, question_id: int, selected_option: str, lang: str = "uz"):
        """Handle inline button answer if fallback buttons are clicked."""
        user = callback.from_user
        async with self.db.get_connection() as conn:
            comp = await queries.get_group_competition(conn, comp_id)
            if not comp or comp.status != "active":
                await callback.answer("Musobaqa yakunlangan.", show_alert=True)
                return

            question = await queries.get_question(conn, question_id)
            if not question:
                return

            correct_opt = next((o for o in question.options if o.is_correct), None)
            is_correct = (correct_opt is not None and correct_opt.option_label == selected_option)
            full_name = f"{user.first_name} {user.last_name or ''}".strip()

            await queries.record_group_answer(
                conn,
                competition_id=comp_id,
                question_id=question_id,
                user_id=user.id,
                username=user.username,
                full_name=full_name,
                selected_option=selected_option,
                is_correct=is_correct,
                response_time_seconds=1.0,
                points=10 if is_correct else 0
            )

        if is_correct:
            await callback.answer("✅ To'g'ri javob! (+10 ball)", show_alert=False)
        else:
            await callback.answer(f"❌ Noto'g'ri! To'g'ri javob: {correct_opt.option_label if correct_opt else ''}", show_alert=False)

