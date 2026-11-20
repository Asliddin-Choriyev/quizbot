import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message, PollAnswer, InlineKeyboardMarkup, InlineKeyboardButton

from bot.database.db import Database
from bot.database import queries
from bot.services.quiz_engine import QuizEngine
from bot.utils.i18n import t
from bot.utils.formatters import escape_html

logger = logging.getLogger(__name__)
router = Router(name="student")

@router.callback_query(F.data.startswith("quiz:start:"))
async def handle_start_quiz(callback: CallbackQuery, db: Database, lang: str = "uz"):
    quiz_id = int(callback.data.split(":")[2])
    engine = QuizEngine(bot=callback.bot, db=db)

    async with db.get_connection() as conn:
        quiz = await queries.get_quiz(conn, quiz_id)
        if not quiz or quiz.question_count == 0:
            await callback.answer("⚠️ This quiz has no questions yet!", show_alert=True)
            return

    await callback.answer("🚀 Test boshlanmoqda...", show_alert=False)
    await engine.start_quiz_session(
        user_id=callback.from_user.id,
        chat_id=callback.message.chat.id,
        quiz_id=quiz_id,
        lang=lang
    )

@router.poll_answer()
async def handle_poll_answer(poll_answer: PollAnswer, db: Database, lang: str = "uz"):
    """Handle instant answer clicks on native Telegram Quiz Polls (both private and group)."""
    # 1. Process individual session
    engine = QuizEngine(bot=poll_answer.bot, db=db)
    await engine.process_poll_answer(poll_answer, lang=lang)

    # 2. Process group competition
    from bot.services.group_engine import GroupQuizEngine
    group_engine = GroupQuizEngine(bot=poll_answer.bot, db=db)
    await group_engine.process_group_poll_answer(poll_answer)

@router.callback_query(F.data.startswith("quiz:pause:"))
async def handle_pause_quiz(callback: CallbackQuery, db: Database, lang: str = "uz"):
    session_id = int(callback.data.split(":")[2])
    engine = QuizEngine(bot=callback.bot, db=db)

    success = await engine.pause_quiz_session(
        session_id=session_id,
        user_id=callback.from_user.id,
        lang=lang
    )
    if not success:
        await callback.answer("Bu test faol emas yoki yakunlangan.", show_alert=True)
        return

    await callback.answer("⏸ Test pauzaga qo'yildi", show_alert=False)

@router.message(Command("pause"))
async def handle_pause_command(message: Message, db: Database, lang: str = "uz"):
    async with db.get_connection() as conn:
        session = await queries.get_active_session_for_user(conn, message.from_user.id)
        if not session:
            await message.answer("Sizda hozirda faol test mavjud emas." if lang == "uz" else "You don't have an active quiz session.")
            return

    engine = QuizEngine(bot=message.bot, db=db)
    await engine.pause_quiz_session(session_id=session.id, user_id=message.from_user.id, lang=lang)

@router.callback_query(F.data.startswith("quiz:resume:"))
async def handle_resume_quiz(callback: CallbackQuery, db: Database, lang: str = "uz"):
    session_id = int(callback.data.split(":")[2])
    engine = QuizEngine(bot=callback.bot, db=db)

    async with db.get_connection() as conn:
        session = await queries.get_session(conn, session_id)
        if not session or session.status != "in_progress":
            await callback.answer("Bu test faol emas.", show_alert=True)
            return

    await callback.answer("▶️ Test davom ettirilmoqda...", show_alert=False)
    try:
        await callback.message.delete()
    except Exception:
        pass

    from bot.services.quiz_engine import reset_consecutive_timeouts
    reset_consecutive_timeouts(session.session_code)
    await engine.send_question(session, lang=lang)

@router.callback_query(F.data.startswith("quiz:finish:"))
async def handle_finish_quiz_early(callback: CallbackQuery, db: Database, lang: str = "uz"):
    session_id = int(callback.data.split(":")[2])
    engine = QuizEngine(bot=callback.bot, db=db)

    async with db.get_connection() as conn:
        session = await queries.get_session(conn, session_id)
        if not session:
            await callback.answer("Session not found.", show_alert=True)
            return

    await callback.answer("⏹ Test yakunlanmoqda...", show_alert=False)
    try:
        await callback.message.delete()
    except Exception:
        pass
    await engine.finish_quiz(session, lang=lang)

@router.callback_query(F.data.startswith("sess:review:"))
async def handle_review_mistakes(callback: CallbackQuery, db: Database, lang: str = "uz"):
    session_id = int(callback.data.split(":")[2])

    async with db.get_connection() as conn:
        session = await queries.get_session(conn, session_id)
        if not session:
            await callback.answer("Session not found.", show_alert=True)
            return

        answers = await queries.get_session_answers_details(conn, session_id)

    # Filter mistakes (incorrect or unanswered)
    mistakes = [a for a in answers if not a["is_correct"]]
    if not mistakes:
        await callback.answer(t("no_mistakes", lang), show_alert=True)
        return

    await callback.answer()
    blocks = [f"🔍 <b>Xatolarni tahlil qilish ({len(mistakes)} ta xato):</b>\n"]

    for idx, m in enumerate(mistakes[:10], start=1):
        your_ans = m["selected_option"] if m["selected_option"] else "<i>Vaqt tugagan / Javob berilmagan</i>"

        async with db.get_connection() as conn:
            question = await queries.get_question(conn, m["question_id"])
            correct_opt = next((o for o in question.options if o.is_correct), None) if question else None
            correct_text = f"{correct_opt.option_label}) {correct_opt.option_text}" if correct_opt else "N/A"

        block = t(
            "review_item",
            lang,
            question=escape_html(m["question_text"]),
            your_ans=escape_html(your_ans),
            correct_ans=escape_html(correct_text),
            explanation=escape_html(m["explanation"] or "Izoh mavjud emas")
        )
        blocks.append(f"<b>#{idx}</b> {block}")

    import config
    can_share = config.can_share_quizzes(callback.from_user.id)
    nav_btn = (
        InlineKeyboardButton(text="📚 Testlar ro'yxati", callback_data="quizzes:list:0")
        if can_share else
        InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="main:menu")
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Qayta topshirish", callback_data=f"quiz:start:{session.quiz_id}")],
        [nav_btn]
    ])

    await callback.message.answer("\n".join(blocks), reply_markup=kb, parse_mode="HTML")
