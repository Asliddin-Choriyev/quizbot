import logging
import config
from aiogram import Router, F
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.enums import ChatType

from bot.database.db import Database
from bot.database import queries
from bot.services.group_engine import GroupQuizEngine
from bot.utils.i18n import t
from bot.utils.formatters import format_leaderboard

logger = logging.getLogger(__name__)
router = Router(name="group")

# Filter for groups and supergroups
router.message.filter(F.chat.type.in_([ChatType.GROUP, ChatType.SUPERGROUP]))

@router.message(Command("quiz"))
async def handle_group_quiz_command(message: Message, command: CommandObject, db: Database, lang: str = "uz"):
    args = command.args
    if not args or not args.isdigit():
        async with db.get_connection() as conn:
            quizzes = await queries.list_quizzes(conn, published_only=True, limit=5)
        if not quizzes:
            await message.reply("ℹ️ No published quizzes available.")
            return
        lines = ["👥 <b>To launch a group competition, use:</b>\n<code>/quiz &lt;quiz_id&gt;</code>\n\n<b>Available Quizzes:</b>"]
        for q in quizzes:
            lines.append(f"• ID <b>{q.id}</b>: {q.title} ({q.question_count} Qs)")
        await message.reply("\n".join(lines), parse_mode="HTML")
        return

    quiz_id = int(args)
    engine = GroupQuizEngine(bot=message.bot, db=db)
    comp_id = await engine.open_lobby(
        chat_id=message.chat.id,
        quiz_id=quiz_id,
        creator_id=message.from_user.id,
        lang=lang
    )
    if not comp_id:
        await message.reply("⚠️ Quiz not found or it has no questions.")

@router.message(CommandStart())
async def handle_group_start(message: Message, command: CommandObject, db: Database, lang: str = "uz"):
    """Handle deep links when bot is added to a group with ?startgroup=quiz_123."""
    args = command.args
    if args and args.startswith("quiz_"):
        try:
            quiz_id = int(args.replace("quiz_", ""))
            engine = GroupQuizEngine(bot=message.bot, db=db)
            await engine.open_lobby(
                chat_id=message.chat.id,
                quiz_id=quiz_id,
                creator_id=message.from_user.id,
                lang=lang
            )
        except ValueError:
            pass

@router.message(Command("stop", "cancel", ignore_mention=True))
async def handle_group_stop_command(message: Message, db: Database, lang: str = "uz"):
    """Allow group creator, competition creator, or admin to stop the active competition."""
    async with db.get_connection() as conn:
        comp = await queries.get_active_group_competition(conn, message.chat.id)
        if not comp:
            await message.reply("ℹ️ Guruhda faol test mavjud emas.")
            return

        user_id = message.from_user.id
        is_allowed = (user_id == comp.created_by) or config.is_admin(user_id)
        if not is_allowed:
            try:
                chat_member = await message.bot.get_chat_member(message.chat.id, user_id)
                if chat_member.status in ("creator", "administrator"):
                    is_allowed = True
            except Exception:
                pass

        if not is_allowed:
            await message.reply("⛔ Faqat testni boshlagan foydalanuvchi yoki guruh adminlari testni to'xtata oladi.")
            return

    engine = GroupQuizEngine(bot=message.bot, db=db)
    await engine.stop_competition(chat_id=message.chat.id, lang=lang)

@router.message(Command("top"))
async def handle_group_top_command(message: Message, db: Database, lang: str = "uz"):
    """Show current standings in the active group quiz on demand."""
    async with db.get_connection() as conn:
        comp = await queries.get_active_group_competition(conn, message.chat.id)
        if not comp:
            await message.reply("ℹ️ Guruhda faol musobaqa yo'q.")
            return
        participants = await queries.get_group_participants(conn, comp.id)

    rankings = [
        {"full_name": p.full_name, "score": p.score, "correct_answers": p.correct_answers}
        for p in participants
    ]
    board_text = format_leaderboard(rankings, max_items=5)
    await message.reply(
        f"📊 <b>Hozirgi yetakchilar ({comp.current_question_index}/{comp.total_questions}):</b>\n\n{board_text}",
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("gjoin:"))
async def handle_group_join_cb(callback: CallbackQuery, db: Database, lang: str = "uz"):
    comp_id = int(callback.data.split(":")[1])
    engine = GroupQuizEngine(bot=callback.bot, db=db)
    await engine.handle_join(callback, comp_id, lang=lang)

@router.callback_query(F.data.startswith("gstart:"))
async def handle_group_start_cb(callback: CallbackQuery, db: Database, lang: str = "uz"):
    comp_id = int(callback.data.split(":")[1])
    engine = GroupQuizEngine(bot=callback.bot, db=db)
    await engine.start_competition(callback, comp_id, lang=lang)

@router.callback_query(F.data.startswith("gans:"))
async def handle_group_answer_cb(callback: CallbackQuery, db: Database, lang: str = "uz"):
    parts = callback.data.split(":")
    # Format: gans:{comp_id}:{question_id}:{selected_option}
    if len(parts) < 4:
        return
    comp_id = int(parts[1])
    question_id = int(parts[2])
    selected_option = parts[3].upper()

    engine = GroupQuizEngine(bot=callback.bot, db=db)
    await engine.process_group_answer(
        callback=callback,
        comp_id=comp_id,
        question_id=question_id,
        selected_option=selected_option,
        lang=lang
    )
