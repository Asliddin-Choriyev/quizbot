import logging
from aiogram import Router, F
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message, CallbackQuery, InlineQuery,
    InlineQueryResultArticle, InputTextMessageContent,
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardRemove
)

from bot.database.db import Database
from bot.database import queries
from bot.keyboards.inline import (
    get_main_menu_kb,
    get_language_kb,
    get_quiz_list_kb,
    get_quiz_landing_kb,
    get_profile_kb
)
from bot.keyboards.reply import (
    get_cancel_reply_kb,
    get_skip_cancel_kb,
    get_phone_request_kb
)
from bot.utils.i18n import t
from bot.utils.formatters import escape_html, format_duration, format_leaderboard

logger = logging.getLogger(__name__)
router = Router(name="common")

class ProfileStates(StatesGroup):
    waiting_name = State()
    waiting_group = State()
    waiting_phone = State()

def format_user_profile_text(user, stats: dict, lang: str = "uz") -> str:
    tg_name = f"{user.first_name or ''} {user.last_name or ''}".strip() or "Anonymous"
    username = f"(@{user.username})" if user.username else ""
    real_name = user.real_name or ("Kiritilmagan" if lang == "uz" else "Not set")
    student_group = user.student_group or ("Kiritilmagan" if lang == "uz" else "Not set")
    phone = user.phone_number or ("Kiritilmagan" if lang == "uz" else "Not set")
    duration = format_duration(stats.get("total_duration", 0.0))
    
    return t(
        "profile_info",
        lang,
        telegram_id=user.telegram_id,
        tg_name=escape_html(tg_name),
        username=escape_html(username),
        real_name=escape_html(real_name),
        student_group=escape_html(student_group),
        phone_number=escape_html(phone),
        total_attempts=stats.get("total_attempts", 0),
        passed_count=stats.get("passed_count", 0),
        avg_score=stats.get("avg_score", 0.0),
        total_correct=stats.get("total_correct", 0),
        total_duration=duration
    )

@router.message(CommandStart())
async def handle_start(message: Message, command: CommandObject, db: Database, lang: str = "uz", is_admin: bool = False):
    args = command.args
    # Check if deep link: e.g. start=quiz_123
    if args and args.startswith("quiz_"):
        try:
            quiz_id = int(args.replace("quiz_", ""))
            bot_info = await message.bot.get_me()
            async with db.get_connection() as conn:
                quiz = await queries.get_quiz(conn, quiz_id)
            if quiz and (quiz.is_published or is_admin):
                text = t(
                    "quiz_landing",
                    lang,
                    title=escape_html(quiz.title),
                    description=escape_html(quiz.description or ""),
                    category=escape_html(quiz.category),
                    question_count=quiz.question_count,
                    timer=quiz.default_timer,
                    pass_percentage=quiz.pass_percentage,
                    shuffle_status=t("enabled" if quiz.shuffle_options else "disabled", lang)
                )
                kb = get_quiz_landing_kb(quiz.id, bot_info.username, lang=lang)
                await message.answer(text, reply_markup=kb, parse_mode="HTML")
                return
        except ValueError:
            pass

    # Standard welcome
    text = t("welcome_title", lang)
    kb = get_main_menu_kb(lang=lang, is_admin=is_admin)
    await message.answer(text, reply_markup=kb, parse_mode="HTML")

@router.message(Command("help"))
async def handle_help(message: Message, lang: str = "uz"):
    await message.answer(t("help_text", lang), parse_mode="HTML")

@router.message(Command("language"))
async def handle_language_command(message: Message, lang: str = "uz"):
    await message.answer(t("choose_language", lang), reply_markup=get_language_kb(), parse_mode="HTML")

@router.message(Command("quizzes"))
async def handle_quizzes_command(message: Message, db: Database, lang: str = "uz"):
    async with db.get_connection() as conn:
        quizzes = await queries.list_quizzes(conn, published_only=True, offset=0, limit=6)
        total = await queries.count_quizzes(conn, published_only=True)

    if not quizzes:
        await message.answer(t("no_quizzes_available", lang), parse_mode="HTML")
        return

    text = t("quiz_list_title", lang)
    kb = get_quiz_list_kb(quizzes, page=0, total_count=total, page_size=6, lang=lang)
    await message.answer(text, reply_markup=kb, parse_mode="HTML")

@router.message(Command("myresults"))
async def handle_myresults_command(message: Message, db: Database, lang: str = "uz"):
    async with db.get_connection() as conn:
        results = await queries.get_user_results(conn, message.from_user.id, limit=10)

    if not results:
        await message.answer("ℹ️ You haven't completed any quizzes yet.", parse_mode="HTML")
        return

    lines = ["📊 <b>Your Recent Quiz Attempts:</b>\n"]
    for r in results:
        status_icon = "✅" if r["passed"] else "❌"
        lines.append(
            f"{status_icon} <b>{escape_html(r['quiz_title'])}</b>\n"
            f"   Score: <b>{r['score_percentage']}%</b> ({r['correct_count']}/{r['total_questions']}) | "
            f"⏱ {format_duration(r['duration_seconds'])}\n"
        )
    await message.answer("\n".join(lines), parse_mode="HTML")

@router.message(Command("profile"))
async def handle_profile_command(message: Message, db: Database, lang: str = "uz"):
    async with db.get_connection() as conn:
        user = await queries.get_user(conn, message.from_user.id)
        stats = await queries.get_user_stats(conn, message.from_user.id)
    if not user:
        return
    text = format_user_profile_text(user, stats, lang=lang)
    kb = get_profile_kb(lang=lang)
    await message.answer(text, reply_markup=kb, parse_mode="HTML")

# ==========================================
# CALLBACK HANDLERS
# ==========================================

@router.callback_query(F.data == "user:profile")
async def cb_user_profile(callback: CallbackQuery, db: Database, lang: str = "uz"):
    async with db.get_connection() as conn:
        user = await queries.get_user(conn, callback.from_user.id)
        stats = await queries.get_user_stats(conn, callback.from_user.id)
    if not user:
        await callback.answer()
        return
    text = format_user_profile_text(user, stats, lang=lang)
    kb = get_profile_kb(lang=lang)
    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "user:edit_profile")
async def cb_user_edit_profile(callback: CallbackQuery, state: FSMContext, lang: str = "uz"):
    await state.set_state(ProfileStates.waiting_name)
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer(
        t("profile_prompt_name", lang),
        reply_markup=get_cancel_reply_kb(lang),
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(ProfileStates.waiting_name)
async def process_profile_name(message: Message, state: FSMContext, lang: str = "uz", is_admin: bool = False):
    if message.text and (message.text == t("btn_cancel", lang) or message.text.lower() in ("/cancel", "cancel")):
        await state.clear()
        await message.answer(t("profile_edit_cancelled", lang), reply_markup=ReplyKeyboardRemove(), parse_mode="HTML")
        await message.answer(t("welcome_title", lang), reply_markup=get_main_menu_kb(lang=lang, is_admin=is_admin), parse_mode="HTML")
        return

    name = message.text.strip() if message.text else ""
    if not name or len(name) < 2:
        await message.reply("⚠️ Iltimos, ism va familiyangizni to'g'ri kiriting:")
        return

    await state.update_data(real_name=name)
    await state.set_state(ProfileStates.waiting_group)
    await message.answer(
        t("profile_prompt_group", lang),
        reply_markup=get_skip_cancel_kb(lang),
        parse_mode="HTML"
    )

@router.message(ProfileStates.waiting_group)
async def process_profile_group(message: Message, state: FSMContext, lang: str = "uz", is_admin: bool = False):
    skip_text = "⏭ O'tkazib yuborish" if lang == "uz" else "⏭ Skip"
    if message.text and (message.text == t("btn_cancel", lang) or message.text.lower() in ("/cancel", "cancel")):
        await state.clear()
        await message.answer(t("profile_edit_cancelled", lang), reply_markup=ReplyKeyboardRemove(), parse_mode="HTML")
        await message.answer(t("welcome_title", lang), reply_markup=get_main_menu_kb(lang=lang, is_admin=is_admin), parse_mode="HTML")
        return

    group_val = None
    if message.text and message.text != skip_text:
        group_val = message.text.strip()

    await state.update_data(student_group=group_val)
    await state.set_state(ProfileStates.waiting_phone)
    await message.answer(
        t("profile_prompt_phone", lang),
        reply_markup=get_phone_request_kb(lang),
        parse_mode="HTML"
    )

@router.message(ProfileStates.waiting_phone)
async def process_profile_phone(message: Message, state: FSMContext, db: Database, lang: str = "uz", is_admin: bool = False):
    skip_text = "⏭ O'tkazib yuborish" if lang == "uz" else "⏭ Skip"
    if message.text and (message.text == t("btn_cancel", lang) or message.text.lower() in ("/cancel", "cancel")):
        await state.clear()
        await message.answer(t("profile_edit_cancelled", lang), reply_markup=ReplyKeyboardRemove(), parse_mode="HTML")
        await message.answer(t("welcome_title", lang), reply_markup=get_main_menu_kb(lang=lang, is_admin=is_admin), parse_mode="HTML")
        return

    phone_val = None
    if message.contact:
        phone_val = message.contact.phone_number
        if not phone_val.startswith("+"):
            phone_val = "+" + phone_val
    elif message.text and message.text != skip_text:
        phone_val = message.text.strip()

    data = await state.get_data()
    await state.clear()

    real_name = data.get("real_name")
    student_group = data.get("student_group")

    async with db.get_connection() as conn:
        await queries.update_user_profile(
            conn,
            telegram_id=message.from_user.id,
            real_name=real_name,
            student_group=student_group,
            phone_number=phone_val
        )
        user = await queries.get_user(conn, message.from_user.id)
        stats = await queries.get_user_stats(conn, message.from_user.id)

    await message.answer(t("profile_updated_success", lang), reply_markup=ReplyKeyboardRemove(), parse_mode="HTML")
    text = format_user_profile_text(user, stats, lang=lang)
    kb = get_profile_kb(lang=lang)
    await message.answer(text, reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data == "main:menu")
async def cb_main_menu(callback: CallbackQuery, lang: str = "uz", is_admin: bool = False):
    text = t("welcome_title", lang)
    kb = get_main_menu_kb(lang=lang, is_admin=is_admin)
    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "user:language")
async def cb_user_language(callback: CallbackQuery, lang: str = "uz"):
    await callback.message.edit_text(t("choose_language", lang), reply_markup=get_language_kb(), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data.startswith("lang:"))
async def cb_set_language(callback: CallbackQuery, db: Database, is_admin: bool = False):
    new_lang = callback.data.split(":")[1]
    async with db.get_connection() as conn:
        await queries.set_user_language(conn, callback.from_user.id, new_lang)

    await callback.answer(t("language_changed", new_lang), show_alert=True)
    text = t("welcome_title", new_lang)
    kb = get_main_menu_kb(lang=new_lang, is_admin=is_admin)
    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        pass

@router.callback_query(F.data.startswith("quizzes:list:"))
async def cb_quiz_list(callback: CallbackQuery, db: Database, lang: str = "uz"):
    page = int(callback.data.split(":")[2])
    limit = 6
    offset = page * limit

    async with db.get_connection() as conn:
        quizzes = await queries.list_quizzes(conn, published_only=True, offset=offset, limit=limit)
        total = await queries.count_quizzes(conn, published_only=True)

    if not quizzes and page == 0:
        await callback.answer(t("no_quizzes_available", lang), show_alert=True)
        return

    text = t("quiz_list_title", lang)
    kb = get_quiz_list_kb(quizzes, page=page, total_count=total, page_size=limit, lang=lang)
    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data.startswith("quiz:view:"))
async def cb_quiz_view(callback: CallbackQuery, db: Database, lang: str = "uz", is_admin: bool = False):
    quiz_id = int(callback.data.split(":")[2])
    bot_info = await callback.bot.get_me()

    async with db.get_connection() as conn:
        quiz = await queries.get_quiz(conn, quiz_id)

    if not quiz or (not quiz.is_published and not is_admin):
        await callback.answer("Quiz not found or unpublished.", show_alert=True)
        return

    text = t(
        "quiz_landing",
        lang,
        title=escape_html(quiz.title),
        description=escape_html(quiz.description or ""),
        category=escape_html(quiz.category),
        question_count=quiz.question_count,
        timer=quiz.default_timer,
        pass_percentage=quiz.pass_percentage,
        shuffle_status=t("enabled" if quiz.shuffle_options else "disabled", lang)
    )
    kb = get_quiz_landing_kb(quiz.id, bot_info.username, lang=lang)
    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Error editing message in cb_quiz_view: {e}")
        try:
            await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
        except Exception as e2:
            logger.error(f"Error answering message in cb_quiz_view: {e2}")
    finally:
        try:
            await callback.answer()
        except Exception:
            pass

@router.callback_query(F.data == "user:results")
async def cb_user_results(callback: CallbackQuery, db: Database, lang: str = "uz"):
    async with db.get_connection() as conn:
        results = await queries.get_user_results(conn, callback.from_user.id, limit=10)

    if not results:
        await callback.answer("You have not taken any quizzes yet!", show_alert=True)
        return

    lines = ["📊 <b>Your Recent Quiz Attempts:</b>\n"]
    for r in results:
        status_icon = "✅" if r["passed"] else "❌"
        lines.append(
            f"{status_icon} <b>{escape_html(r['quiz_title'])}</b>\n"
            f"   Score: <b>{r['score_percentage']}%</b> ({r['correct_count']}/{r['total_questions']}) | "
            f"⏱ {format_duration(r['duration_seconds'])}\n"
        )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Back", callback_data="main:menu")]
    ])
    await callback.message.edit_text("\n".join(lines), reply_markup=kb, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data.startswith("quiz:leaderboard:"))
async def cb_quiz_leaderboard(callback: CallbackQuery, db: Database, lang: str = "uz"):
    quiz_id = int(callback.data.split(":")[2])
    async with db.get_connection() as conn:
        quiz = await queries.get_quiz(conn, quiz_id)
        leaders = await queries.get_quiz_leaderboard(conn, quiz_id, limit=10)

    board_text = format_leaderboard(leaders, max_items=10)
    text = f"🏆 <b>Top Students — {escape_html(quiz.title if quiz else 'Quiz')}</b>\n\n{board_text}"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Back", callback_data=f"quiz:view:{quiz_id}")]
    ])
    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()

# ==========================================
# INLINE QUERY HANDLER (FOR SHARING LIKE @QuizBot)
# ==========================================

@router.inline_query()
async def handle_inline_query(inline_query: InlineQuery, db: Database, lang: str = "uz"):
    query = inline_query.query.strip().lower()
    async with db.get_connection() as conn:
        quizzes = await queries.list_quizzes(conn, published_only=True, limit=20)

    bot_info = await inline_query.bot.get_me()
    bot_name = bot_info.username or "quizzes_makerbot"

    results = []
    for q in quizzes:
        # Match query by ID or title substring
        if query:
            clean_q = query.replace("quiz_", "")
            if str(q.id) != clean_q and query not in q.title.lower():
                continue

        text = (
            f"🎲 <b>“{escape_html(q.title)}”</b>\n"
            f"{escape_html(q.description or '')}\n\n"
            f"🖋 <i>{q.question_count} ta savol · ⏱ {q.default_timer} soniya</i>"
        )

        start_text = "Bu testni boshlash" if lang == "uz" else "Start this quiz"
        group_text = "Guruhda testni boshlash" if lang == "uz" else "Start in Group"
        share_text = "Testni ulashish" if lang == "uz" else "Share quiz"

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text=start_text, url=f"https://t.me/{bot_name}?start=quiz_{q.id}")
            ],
            [
                InlineKeyboardButton(text=group_text, url=f"https://t.me/{bot_name}?startgroup=quiz_{q.id}")
            ],
            [
                InlineKeyboardButton(text=share_text, switch_inline_query=str(q.id))
            ]
        ])

        results.append(
            InlineQueryResultArticle(
                id=f"quiz_{q.id}",
                title=f"🎲 {q.title}",
                description=f"🖋 {q.question_count} ta savol · ⏱ {q.default_timer} soniya",
                input_message_content=InputTextMessageContent(
                    message_text=text,
                    parse_mode="HTML"
                ),
                reply_markup=kb
            )
        )

    await inline_query.answer(results, cache_time=1, is_personal=True)
