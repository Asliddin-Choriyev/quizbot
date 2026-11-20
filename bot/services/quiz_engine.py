import asyncio
import logging
import time
import random
from pathlib import Path
from typing import Dict, Optional, Any, List
from aiogram import Bot
from aiogram.types import PollAnswer, FSInputFile

import config
from bot.database.db import Database
from bot.database import queries
from bot.database.models import Quiz, Question, QuizSession, QuestionOption
from bot.keyboards.inline import get_quiz_completed_kb, get_quiz_paused_kb, get_quiz_in_progress_kb
from bot.utils.i18n import t
from bot.utils.formatters import escape_html, format_duration

logger = logging.getLogger(__name__)

# Active poll registry: poll_id -> dict
_active_individual_polls: Dict[str, Dict[str, Any]] = {}
# Active session timers: session_code -> asyncio.Task
_active_session_timers: Dict[str, asyncio.Task] = {}
# Consecutive timeouts counter: session_code -> count
_consecutive_timeouts: Dict[str, int] = {}
# Cached Telegram file IDs for images: image_path -> file_id
_cached_file_ids: Dict[str, str] = {}

def cancel_session_timer(session_code: str):
    task = _active_session_timers.pop(session_code, None)
    try:
        current = asyncio.current_task()
    except RuntimeError:
        current = None
    if task and task != current and not task.done():
        task.cancel()

def reset_consecutive_timeouts(session_code: str):
    _consecutive_timeouts[session_code] = 0

class QuizEngine:
    def __init__(self, bot: Bot, db: Database):
        self.bot = bot
        self.db = db

    async def start_quiz_session(self, user_id: int, chat_id: int, quiz_id: int, lang: str = "uz") -> Optional[QuizSession]:
        """Initialize and launch an individual quiz session using native Telegram Quiz Polls."""
        async with self.db.get_connection() as conn:
            quiz = await queries.get_quiz(conn, quiz_id)
            if not quiz:
                return None

            question_ids = await queries.get_question_ids_by_quiz(conn, quiz_id)
            if not question_ids:
                return None

            # Cancel any existing active session timer for this user
            existing = await queries.get_active_session_for_user(conn, user_id)
            if existing:
                cancel_session_timer(existing.session_code)
                await queries.update_session(conn, existing.id, status="abandoned")

            import uuid
            session_code = f"s_{uuid.uuid4().hex[:12]}"

            session_id = await queries.create_session(
                conn,
                session_code=session_code,
                quiz_id=quiz_id,
                user_id=user_id,
                chat_id=chat_id,
                total_questions=len(question_ids),
                question_ids=question_ids
            )
            session = await queries.get_session(conn, session_id)

        reset_consecutive_timeouts(session.session_code)

        # Send first question poll
        await self.send_question(session, lang=lang)
        return session

    async def send_question(self, session: QuizSession, lang: str = "uz"):
        """Render and send current question as a native Telegram Quiz Poll with real-time timer."""
        cancel_session_timer(session.session_code)

        if session.current_question_index >= session.total_questions:
            await self.finish_quiz(session, lang=lang)
            return

        question_id = session.question_ids_order[session.current_question_index]

        async with self.db.get_connection() as conn:
            quiz = await queries.get_quiz(conn, session.quiz_id)
            question = await queries.get_question(conn, question_id)

        if not question or not quiz:
            await self.finish_quiz(session, lang=lang)
            return

        # Determine timer (Telegram open_period: 5 to 600s)
        timer = question.timer_seconds or quiz.default_timer or 25
        timer = max(5, min(600, timer))

        # Prepare options
        options = list(question.options)
        if quiz.shuffle_options:
            random.shuffle(options)

        # Find correct option index
        correct_idx = next((i for i, opt in enumerate(options) if opt.is_correct), 0)

        # Telegram poll constraints: question <= 300 chars, option <= 100 chars, explanation <= 200 chars
        curr_idx = session.current_question_index + 1
        prefix = f"[{curr_idx}/{session.total_questions}] "
        q_text = prefix + question.question_text
        if len(q_text) > 300:
            q_text = q_text[:297] + "..."

        opt_texts = []
        for opt in options:
            txt = opt.option_text.strip()
            if len(txt) > 100:
                txt = txt[:97] + "..."
            opt_texts.append(txt)

        exp_text = None
        if quiz.show_explanation and question.explanation:
            exp_text = question.explanation.strip()
            if len(exp_text) > 200:
                exp_text = exp_text[:197] + "..."

        # Send question image if available
        photo_msg_id = None
        if question.image_url:
            try:
                cached_id = _cached_file_ids.get(question.image_url)
                if cached_id:
                    p_msg = await self.bot.send_photo(chat_id=session.chat_id, photo=cached_id, protect_content=True)
                    if p_msg:
                        photo_msg_id = p_msg.message_id
                else:
                    img_path = Path(question.image_url)
                    if not img_path.is_absolute():
                        img_path = config.BASE_DIR / img_path
                    if img_path.exists():
                        photo_msg = await self.bot.send_photo(chat_id=session.chat_id, photo=FSInputFile(str(img_path)), protect_content=True)
                        if photo_msg and photo_msg.photo:
                            _cached_file_ids[question.image_url] = photo_msg.photo[-1].file_id
                            photo_msg_id = photo_msg.message_id
                    elif question.image_url.startswith(("http://", "https://")):
                        photo_msg = await self.bot.send_photo(chat_id=session.chat_id, photo=question.image_url, protect_content=True)
                        if photo_msg and photo_msg.photo:
                            _cached_file_ids[question.image_url] = photo_msg.photo[-1].file_id
                            photo_msg_id = photo_msg.message_id
            except Exception as e:
                logger.warning(f"Error sending quiz question image: {e}")

        try:
            poll_msg = await self.bot.send_poll(
                chat_id=session.chat_id,
                question=q_text,
                options=opt_texts,
                type="quiz",
                correct_option_id=correct_idx,
                explanation=exp_text,
                open_period=timer,
                is_anonymous=False,
                reply_markup=get_quiz_in_progress_kb(session.id, lang=lang),
                protect_content=True
            )
        except Exception as e:
            logger.error(f"Error sending quiz poll: {e}")
            return

        # Register active poll mapping
        poll_id = poll_msg.poll.id
        _active_individual_polls[poll_id] = {
            "session_code": session.session_code,
            "session_id": session.id,
            "message_id": poll_msg.message_id,
            "photo_message_id": photo_msg_id,
            "quiz_id": session.quiz_id,
            "question_id": question.id,
            "user_id": session.user_id,
            "chat_id": session.chat_id,
            "options": options,
            "correct_idx": correct_idx,
            "start_time": time.time(),
            "timer": timer
        }

        # Schedule automatic timeout handling when open_period expires
        timer_task = asyncio.create_task(
            self._handle_poll_timeout(session.session_code, question.id, poll_id, timer, lang)
        )
        _active_session_timers[session.session_code] = timer_task

    async def _handle_poll_timeout(
        self,
        session_code: str,
        question_id: int,
        poll_id: str,
        timer_seconds: int,
        lang: str
    ):
        """Called when real-time countdown reaches 0:00 and user has NOT answered."""
        try:
            # Wait slightly past open_period so Telegram client closes the poll
            await asyncio.sleep(timer_seconds + 0.5)
        except asyncio.CancelledError:
            return

        poll_data = _active_individual_polls.pop(poll_id, None)
        if not poll_data:
            return

        chat_id = poll_data["chat_id"]
        message_id = poll_data.get("message_id")

        # Stop poll on Telegram to reveal correct answer natively
        if message_id:
            try:
                await self.bot.stop_poll(chat_id=chat_id, message_id=message_id)
            except Exception:
                pass

        async with self.db.get_connection() as conn:
            session = await queries.get_session_by_code(conn, session_code)
            if not session or session.status != "in_progress":
                return

            current_q_id = session.question_ids_order[session.current_question_index]
            if current_q_id != question_id:
                return

            question = await queries.get_question(conn, question_id)

            # Record unanswered
            await queries.record_answer(
                conn,
                session_id=session.id,
                question_id=question_id,
                user_id=session.user_id,
                selected_option=None,
                is_correct=False,
                response_time_seconds=float(timer_seconds)
            )

            await queries.update_session(
                conn,
                session.id,
                unanswered_count=session.unanswered_count + 1,
                current_question_index=session.current_question_index + 1
            )
            session = await queries.get_session(conn, session.id)

        # Track consecutive timeouts
        timeouts = _consecutive_timeouts.get(session_code, 0) + 1
        _consecutive_timeouts[session_code] = timeouts

        # If user walked away (3 consecutive unanswered questions), pause the quiz
        if timeouts >= 3 and session.current_question_index < session.total_questions:
            pause_text = (
                f"⏸ <b>Test to'xtatildi</b>\n\n"
                f"Ketma-ket {timeouts} ta savolga javob berilmadi. Qaytganingizda davom ettirishingiz mumkin:"
            )
            kb = get_quiz_paused_kb(session.id, lang=lang)
            await self.bot.send_message(chat_id=chat_id, text=pause_text, reply_markup=kb, parse_mode="HTML")
            return

        # Brief pause (1.2s) so student sees the green correct answer on the closed poll
        await asyncio.sleep(1.2)

        # Automatically advance to next question with fresh timer
        await self.send_question(session, lang=lang)

    async def process_poll_answer(self, poll_answer: PollAnswer, lang: str = "uz"):
        """Called immediately when user taps an answer option on the Telegram Quiz Poll."""
        poll_id = poll_answer.poll_id
        poll_data = _active_individual_polls.get(poll_id)
        if not poll_data:
            return

        # Ensure answer comes from the session owner
        if poll_answer.user.id != poll_data["user_id"]:
            return

        if not poll_answer.option_ids:
            return

        # Cancel timeout task immediately
        cancel_session_timer(poll_data["session_code"])
        _active_individual_polls.pop(poll_id, None)

        # Reset consecutive timeouts counter
        reset_consecutive_timeouts(poll_data["session_code"])

        start_time = poll_data.get("start_time", time.time())
        response_time = round(time.time() - start_time, 2)

        selected_idx = poll_answer.option_ids[0]
        selected_opt = poll_data["options"][selected_idx]
        is_correct = (selected_idx == poll_data["correct_idx"])

        async with self.db.get_connection() as conn:
            session = await queries.get_session_by_code(conn, poll_data["session_code"])
            if not session or session.status != "in_progress":
                return

            await queries.record_answer(
                conn,
                session_id=session.id,
                question_id=poll_data["question_id"],
                user_id=session.user_id,
                selected_option=selected_opt.option_label,
                is_correct=is_correct,
                response_time_seconds=response_time
            )

            new_correct = session.correct_count + (1 if is_correct else 0)
            new_incorrect = session.incorrect_count + (0 if is_correct else 1)
            new_index = session.current_question_index + 1

            await queries.update_session(
                conn,
                session.id,
                correct_count=new_correct,
                incorrect_count=new_incorrect,
                current_question_index=new_index
            )
            session = await queries.get_session(conn, session.id)

        # Brief pause (1.2s) so user sees Telegram's native animation / confetti
        await asyncio.sleep(1.2)

        # Move to next question immediately, restarting timer from beginning
        await self.send_question(session, lang=lang)

    async def pause_quiz_session(self, session_id: int, user_id: int, lang: str = "uz") -> bool:
        """Manually pause an ongoing quiz session, cancel its timer, remove pending poll, and show paused controls."""
        async with self.db.get_connection() as conn:
            session = await queries.get_session(conn, session_id)
            if not session or session.status != "in_progress":
                return False
            if session.user_id != user_id:
                return False

        # Cancel active timer task
        cancel_session_timer(session.session_code)
        reset_consecutive_timeouts(session.session_code)

        # Find active poll from registry
        found_poll_id = None
        poll_info = None
        for pid, pdata in list(_active_individual_polls.items()):
            if pdata.get("session_id") == session.id or pdata.get("session_code") == session.session_code:
                found_poll_id = pid
                poll_info = pdata
                break

        if found_poll_id:
            _active_individual_polls.pop(found_poll_id, None)

        # Clean up the uncompleted poll and photo so user cannot click or see answers while paused
        if poll_info:
            chat_id = poll_info.get("chat_id", session.chat_id)
            poll_msg_id = poll_info.get("message_id")
            photo_msg_id = poll_info.get("photo_message_id")

            if poll_msg_id:
                try:
                    await self.bot.delete_message(chat_id=chat_id, message_id=poll_msg_id)
                except Exception:
                    try:
                        await self.bot.stop_poll(chat_id=chat_id, message_id=poll_msg_id)
                    except Exception:
                        pass

            if photo_msg_id:
                try:
                    await self.bot.delete_message(chat_id=chat_id, message_id=photo_msg_id)
                except Exception:
                    pass

        curr_q = session.current_question_index + 1
        total_q = session.total_questions
        correct_cnt = session.correct_count
        incorrect_cnt = session.incorrect_count

        if lang == "uz":
            pause_text = (
                f"⏸ <b>Test vaqtincha to'xtatildi (pauza)</b>\n\n"
                f"📊 <b>Hozirgi holat:</b>\n"
                f"• Savol: <b>{curr_q}/{total_q}</b>\n"
                f"• To'g'ri javoblar: <b>{correct_cnt}</b> ta\n"
                f"• Noto'g'ri javoblar: <b>{incorrect_cnt}</b> ta\n\n"
                f"Tayyor bo'lganingizda davom ettirishingiz yoki testni yakunlashingiz mumkin:"
            )
        else:
            pause_text = (
                f"⏸ <b>Quiz Paused</b>\n\n"
                f"📊 <b>Current Progress:</b>\n"
                f"• Question: <b>{curr_q}/{total_q}</b>\n"
                f"• Correct: <b>{correct_cnt}</b>\n"
                f"• Incorrect: <b>{incorrect_cnt}</b>\n\n"
                f"You can resume or finish whenever you are ready:"
            )

        kb = get_quiz_paused_kb(session.id, lang=lang)
        await self.bot.send_message(
            chat_id=session.chat_id,
            text=pause_text,
            reply_markup=kb,
            parse_mode="HTML"
        )
        return True

    async def finish_quiz(self, session: QuizSession, lang: str = "uz"):
        """Compute final metrics and render the completion score card."""
        cancel_session_timer(session.session_code)
        reset_consecutive_timeouts(session.session_code)

        async with self.db.get_connection() as conn:
            quiz = await queries.get_quiz(conn, session.quiz_id)
            total = session.total_questions or 1
            score_pct = round((session.correct_count / total) * 100.0, 1)
            passed = score_pct >= (quiz.pass_percentage if quiz else 60)

            # Calculate duration
            async with conn.execute(
                "SELECT COALESCE(SUM(response_time_seconds), 0.0) FROM session_answers WHERE session_id = ?",
                (session.id,)
            ) as cursor:
                row = await cursor.fetchone()
                total_duration = row[0] if row else 0.0

            await queries.complete_session(
                conn,
                session_id=session.id,
                correct=session.correct_count,
                incorrect=session.incorrect_count,
                unanswered=session.unanswered_count,
                score_percentage=score_pct,
                passed=passed,
                duration_seconds=total_duration
            )

        status_badge = t("passed_badge" if passed else "failed_badge", lang)
        summary_text = t(
            "quiz_completed_title",
            lang,
            title=escape_html(quiz.title if quiz else "Quiz"),
            status_badge=status_badge,
            total=session.total_questions,
            correct=session.correct_count,
            score_pct=score_pct,
            incorrect=session.incorrect_count,
            unanswered=session.unanswered_count,
            duration=format_duration(total_duration),
            pass_threshold=quiz.pass_percentage if quiz else 60
        )

        has_mistakes = (session.incorrect_count + session.unanswered_count) > 0
        can_share = config.can_share_quizzes(session.user_id)
        kb = get_quiz_completed_kb(session.id, session.quiz_id, has_mistakes=has_mistakes, lang=lang, can_share=can_share)

        await self.bot.send_message(
            chat_id=session.chat_id,
            text=summary_text,
            reply_markup=kb,
            parse_mode="HTML"
        )
