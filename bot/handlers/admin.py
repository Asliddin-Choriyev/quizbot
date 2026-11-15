import os
import uuid
import logging
from pathlib import Path
from typing import Dict, Any

from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message, CallbackQuery, FSInputFile,
    InlineKeyboardMarkup, InlineKeyboardButton
)

import config
from bot.database.db import Database
from bot.database import queries
from bot.keyboards.inline import (
    get_admin_menu_kb,
    get_admin_quizzes_kb,
    get_admin_quiz_manage_kb,
    get_admin_timer_options_kb,
    get_admin_pass_mark_options_kb,
    get_admin_delete_confirm_kb,
    get_import_confirm_kb,
    get_admin_users_kb,
    get_admin_user_detail_kb,
    get_admin_user_delete_confirm_kb,
    get_admin_clear_users_confirm_kb
)
from bot.services.importer import (
    parse_import_file,
    create_sample_excel_template,
    create_sample_csv_template
)
from bot.services.exporter import export_quiz_results_to_excel, export_all_users_to_excel
from bot.utils.i18n import t
from bot.utils.formatters import escape_html

logger = logging.getLogger(__name__)
router = Router(name="admin")

# Pending imports registry: token -> dict
_pending_imports: Dict[str, Dict[str, Any]] = {}

# ==========================================
# FSM STATES
# ==========================================

class CreateQuizStates(StatesGroup):
    waiting_title = State()
    waiting_description = State()
    waiting_category = State()

class AddQuestionStates(StatesGroup):
    waiting_question_text = State()
    waiting_option_a = State()
    waiting_option_b = State()
    waiting_option_c = State()
    waiting_option_d = State()
    waiting_correct = State()
    waiting_explanation = State()

class CustomTimerStates(StatesGroup):
    waiting_timer_seconds = State()

class ImportFileStates(StatesGroup):
    waiting_file = State()

# Guard: Ensure only admins can execute these handlers
@router.message(Command("admin"))
async def handle_admin_command(message: Message, db: Database, is_admin: bool = False, lang: str = "uz"):
    if not is_admin:
        await message.reply(t("admin_not_authorized", lang))
        return

    async with db.get_connection() as conn:
        quiz_count = await queries.count_quizzes(conn)
        question_count = await queries.count_questions(conn)
        user_count = await queries.count_users(conn)

    text = t(
        "admin_welcome",
        lang,
        quiz_count=quiz_count,
        question_count=question_count,
        user_count=user_count
    )
    kb = get_admin_menu_kb(lang=lang)
    await message.answer(text, reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data.in_(["adm:menu", "admin:menu"]))
async def cb_admin_menu(callback: CallbackQuery, db: Database, is_admin: bool = False, lang: str = "uz", state: FSMContext = None):
    if state:
        await state.clear()
    if not is_admin:
        await callback.answer(t("admin_not_authorized", lang), show_alert=True)
        return

    async with db.get_connection() as conn:
        quiz_count = await queries.count_quizzes(conn)
        question_count = await queries.count_questions(conn)
        user_count = await queries.count_users(conn)

    text = t(
        "admin_welcome",
        lang,
        quiz_count=quiz_count,
        question_count=question_count,
        user_count=user_count
    )
    kb = get_admin_menu_kb(lang=lang)
    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()

# ==========================================
# MANAGE QUIZZES
# ==========================================

@router.callback_query(F.data.startswith("adm:quizzes:"))
async def cb_admin_quizzes(callback: CallbackQuery, db: Database, is_admin: bool = False, lang: str = "uz"):
    if not is_admin:
        return
    page = int(callback.data.split(":")[2])
    limit = 6
    offset = page * limit

    async with db.get_connection() as conn:
        quizzes = await queries.list_quizzes(conn, published_only=False, offset=offset, limit=limit)
        total = await queries.count_quizzes(conn, published_only=False)

    text = f"📋 <b>Quiz Management</b> (Total: {total})\nSelect a quiz to manage:"
    kb = get_admin_quizzes_kb(quizzes, page=page, total=total, page_size=limit)
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data.startswith("adm:quiz:"))
async def cb_admin_quiz_detail(callback: CallbackQuery, db: Database, is_admin: bool = False, lang: str = "uz"):
    if not is_admin:
        return
    quiz_id = int(callback.data.split(":")[2])
    async with db.get_connection() as conn:
        quiz = await queries.get_quiz(conn, quiz_id)
        stats = await queries.get_quiz_stats(conn, quiz_id)

    if not quiz:
        await callback.answer("Quiz not found.", show_alert=True)
        return

    text = (
        f"🎯 <b>Quiz: {escape_html(quiz.title)}</b>\n\n"
        f"📝 <i>{escape_html(quiz.description or 'No description')}</i>\n"
        f"📂 Category: <b>{escape_html(quiz.category)}</b>\n"
        f"❓ Questions: <b>{quiz.question_count}</b>\n"
        f"⏱ Default Timer: <b>{quiz.default_timer}s</b>\n"
        f"🎯 Pass Mark: <b>{quiz.pass_percentage}%</b>\n"
        f"🌐 Status: <b>{'🟢 Published' if quiz.is_published else '🔴 Unpublished'}</b>\n\n"
        f"📊 <b>Performance Stats:</b>\n"
        f"• Total completions: <b>{stats['total_plays']}</b>\n"
        f"• Average score: <b>{stats['avg_score']}%</b>\n"
        f"• Pass rate: <b>{stats['pass_rate']}%</b> ({stats['passed_count']} passed)\n"
        f"• Avg duration: <b>{stats['avg_duration']}s</b>"
    )
    kb = get_admin_quiz_manage_kb(quiz, lang=lang)
    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()

# ==========================================
# QUIZ SETTINGS TOGGLES
# ==========================================

@router.callback_query(F.data.startswith("adm:togpub:"))
async def cb_toggle_publish(callback: CallbackQuery, db: Database, is_admin: bool = False, lang: str = "uz"):
    if not is_admin:
        return
    quiz_id = int(callback.data.split(":")[2])
    async with db.get_connection() as conn:
        await queries.toggle_quiz_publish(conn, quiz_id)
    await cb_admin_quiz_detail(callback, db, is_admin, lang)

@router.callback_query(F.data.startswith("adm:togshuf:"))
async def cb_toggle_shuffle(callback: CallbackQuery, db: Database, is_admin: bool = False, lang: str = "uz"):
    if not is_admin:
        return
    quiz_id = int(callback.data.split(":")[2])
    async with db.get_connection() as conn:
        quiz = await queries.get_quiz(conn, quiz_id)
        if quiz:
            await queries.update_quiz(conn, quiz_id, shuffle_options=not quiz.shuffle_options)
    await cb_admin_quiz_detail(callback, db, is_admin, lang)

@router.callback_query(F.data.startswith("adm:togexp:"))
async def cb_toggle_explanation(callback: CallbackQuery, db: Database, is_admin: bool = False, lang: str = "uz"):
    if not is_admin:
        return
    quiz_id = int(callback.data.split(":")[2])
    async with db.get_connection() as conn:
        quiz = await queries.get_quiz(conn, quiz_id)
        if quiz:
            await queries.update_quiz(conn, quiz_id, show_explanation=not quiz.show_explanation)
    await cb_admin_quiz_detail(callback, db, is_admin, lang)

@router.callback_query(F.data.startswith("adm:settimer:"))
async def cb_set_timer_menu(callback: CallbackQuery, is_admin: bool = False):
    if not is_admin:
        return
    quiz_id = int(callback.data.split(":")[2])
    kb = get_admin_timer_options_kb(quiz_id)
    await callback.message.edit_text("⏱ <b>Select timer per question:</b>", reply_markup=kb, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data.startswith("adm:savetimer:"))
async def cb_save_timer(callback: CallbackQuery, db: Database, is_admin: bool = False, lang: str = "uz"):
    if not is_admin:
        return
    parts = callback.data.split(":")
    quiz_id = int(parts[2])
    seconds = int(parts[3])
    async with db.get_connection() as conn:
        await queries.update_quiz(conn, quiz_id, default_timer=seconds)
    await callback.answer(f"Timer set to {seconds}s!", show_alert=False)
    await cb_admin_quiz_detail(callback, db, is_admin, lang)

@router.callback_query(F.data.startswith("adm:setpass:"))
async def cb_set_pass_menu(callback: CallbackQuery, is_admin: bool = False):
    if not is_admin:
        return
    quiz_id = int(callback.data.split(":")[2])
    kb = get_admin_pass_mark_options_kb(quiz_id)
    await callback.message.edit_text("🎯 <b>Select passing threshold percentage:</b>", reply_markup=kb, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data.startswith("adm:savepass:"))
async def cb_save_pass(callback: CallbackQuery, db: Database, is_admin: bool = False, lang: str = "uz"):
    if not is_admin:
        return
    parts = callback.data.split(":")
    quiz_id = int(parts[2])
    pct = int(parts[3])
    async with db.get_connection() as conn:
        await queries.update_quiz(conn, quiz_id, pass_percentage=pct)
    await callback.answer(f"Passing threshold set to {pct}%!", show_alert=False)
    await cb_admin_quiz_detail(callback, db, is_admin, lang)

@router.callback_query(F.data.startswith("adm:delconf:"))
async def cb_del_confirm(callback: CallbackQuery, is_admin: bool = False):
    if not is_admin:
        return
    quiz_id = int(callback.data.split(":")[2])
    kb = get_admin_delete_confirm_kb(quiz_id)
    await callback.message.edit_text(
        "⚠️ <b>Are you sure you want to permanently delete this quiz and all its questions?</b>",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("adm:delquiz:"))
async def cb_delete_quiz(callback: CallbackQuery, db: Database, is_admin: bool = False, lang: str = "uz"):
    if not is_admin:
        return
    quiz_id = int(callback.data.split(":")[2])
    async with db.get_connection() as conn:
        await queries.delete_quiz(conn, quiz_id)
    await callback.answer(t("quiz_deleted_success", lang), show_alert=True)
    await cb_admin_quizzes(callback, db, is_admin, lang)

# ==========================================
# CREATE QUIZ FSM
# ==========================================

@router.callback_query(F.data == "adm:create_quiz")
async def cb_start_create_quiz(callback: CallbackQuery, state: FSMContext, is_admin: bool = False):
    if not is_admin:
        return
    await state.set_state(CreateQuizStates.waiting_title)
    await callback.message.answer(
        "➕ <b>Create New Quiz (Step 1/3):</b>\n\nEnter the title for the new quiz:\n(Or send /cancel to abort)",
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(Command("cancel"), StateFilter("*"))
async def handle_cancel_fsm(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Action cancelled. Returning to main menu.")

@router.message(CreateQuizStates.waiting_title)
async def fsm_quiz_title(message: Message, state: FSMContext):
    title = message.text.strip()
    if len(title) < 2:
        await message.reply("Title is too short. Please enter a valid title:")
        return
    await state.update_data(title=title)
    await state.set_state(CreateQuizStates.waiting_description)
    await message.answer("📝 <b>Step 2/3:</b> Enter a brief description for this quiz (or type 'None'):", parse_mode="HTML")

@router.message(CreateQuizStates.waiting_description)
async def fsm_quiz_desc(message: Message, state: FSMContext):
    desc = message.text.strip()
    if desc.lower() in ("none", "yo'q", "-"):
        desc = ""
    await state.update_data(description=desc)
    await state.set_state(CreateQuizStates.waiting_category)
    await message.answer("📂 <b>Step 3/3:</b> Enter subject or category (e.g. Science, History, Tech):", parse_mode="HTML")

@router.message(CreateQuizStates.waiting_category)
async def fsm_quiz_cat(message: Message, state: FSMContext, db: Database, lang: str = "uz"):
    category = message.text.strip() or "General"
    data = await state.get_data()
    await state.clear()

    async with db.get_connection() as conn:
        quiz_id = await queries.create_quiz(
            conn,
            title=data["title"],
            description=data["description"],
            category=category,
            default_timer=30,
            shuffle_options=True,
            show_explanation=True,
            pass_percentage=60,
            is_published=True,
            created_by=message.from_user.id
        )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📥 Import Questions Now", callback_data=f"adm:import:{quiz_id}")],
        [InlineKeyboardButton(text="➕ Add Question Manually", callback_data=f"adm:add_q:{quiz_id}")],
        [InlineKeyboardButton(text="📋 Manage Quiz", callback_data=f"adm:quiz:{quiz_id}")]
    ])
    await message.answer(
        t("quiz_created_success", lang, title=escape_html(data["title"])),
        reply_markup=kb,
        parse_mode="HTML"
    )

# ==========================================
# PREVIEW & ADD QUESTIONS MANUALLY
# ==========================================

@router.callback_query(F.data.startswith("adm:preview:"))
async def cb_preview_questions(callback: CallbackQuery, db: Database, is_admin: bool = False):
    if not is_admin:
        return
    parts = callback.data.split(":")
    quiz_id = int(parts[2])
    idx = int(parts[3])

    async with db.get_connection() as conn:
        q_ids = await queries.get_question_ids_by_quiz(conn, quiz_id)
        if not q_ids:
            await callback.answer("No questions in this quiz yet.", show_alert=True)
            return

        if idx >= len(q_ids):
            idx = 0
        elif idx < 0:
            idx = len(q_ids) - 1

        question = await queries.get_question(conn, q_ids[idx])

    opts_lines = []
    for opt in question.options:
        marker = "✅" if opt.is_correct else "🔘"
        opts_lines.append(f"{marker} <b>{opt.option_label})</b> {escape_html(opt.option_text)}")

    text = (
        f"👁 <b>Question Preview ({idx + 1} of {len(q_ids)}):</b>\n\n"
        f"<b>{escape_html(question.question_text)}</b>\n\n"
        + "\n".join(opts_lines) +
        f"\n\n💡 <b>Explanation:</b> {escape_html(question.explanation or 'None')}\n"
        f"⏱ <b>Timer:</b> {question.timer_seconds or 'Default'}s | Difficulty: {question.difficulty}"
    )

    nav = [
        InlineKeyboardButton(text="◀️ Prev", callback_data=f"adm:preview:{quiz_id}:{idx - 1}"),
        InlineKeyboardButton(text=f"{idx + 1}/{len(q_ids)}", callback_data="noop"),
        InlineKeyboardButton(text="Next ▶️", callback_data=f"adm:preview:{quiz_id}:{idx + 1}")
    ]
    rows = [
        nav,
        [
            InlineKeyboardButton(text="🗑 Delete This Question", callback_data=f"adm:del_q:{question.id}:{quiz_id}"),
            InlineKeyboardButton(text="◀️ Back to Quiz", callback_data=f"adm:quiz:{quiz_id}")
        ]
    ]
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=rows), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data.startswith("adm:del_q:"))
async def cb_delete_single_question(callback: CallbackQuery, db: Database, is_admin: bool = False):
    if not is_admin:
        return
    parts = callback.data.split(":")
    q_id = int(parts[2])
    quiz_id = int(parts[3])

    async with db.get_connection() as conn:
        await queries.delete_question(conn, q_id)

    await callback.answer("Question deleted.", show_alert=False)
    await cb_preview_questions(callback, db, is_admin)

@router.callback_query(F.data.startswith("adm:add_q:"))
async def cb_start_add_question(callback: CallbackQuery, state: FSMContext, is_admin: bool = False):
    if not is_admin:
        return
    quiz_id = int(callback.data.split(":")[2])
    await state.update_data(quiz_id=quiz_id)
    await state.set_state(AddQuestionStates.waiting_question_text)
    await callback.message.answer("✏️ <b>Enter the Question text:</b>\n(Or send /cancel to abort)", parse_mode="HTML")
    await callback.answer()

@router.message(AddQuestionStates.waiting_question_text)
async def fsm_q_text(message: Message, state: FSMContext):
    await state.update_data(question_text=message.text.strip())
    await state.set_state(AddQuestionStates.waiting_option_a)
    await message.answer("Enter <b>Option A</b>:", parse_mode="HTML")

@router.message(AddQuestionStates.waiting_option_a)
async def fsm_opt_a(message: Message, state: FSMContext):
    await state.update_data(option_a=message.text.strip())
    await state.set_state(AddQuestionStates.waiting_option_b)
    await message.answer("Enter <b>Option B</b>:", parse_mode="HTML")

@router.message(AddQuestionStates.waiting_option_b)
async def fsm_opt_b(message: Message, state: FSMContext):
    await state.update_data(option_b=message.text.strip())
    await state.set_state(AddQuestionStates.waiting_option_c)
    await message.answer("Enter <b>Option C</b>:", parse_mode="HTML")

@router.message(AddQuestionStates.waiting_option_c)
async def fsm_opt_c(message: Message, state: FSMContext):
    await state.update_data(option_c=message.text.strip())
    await state.set_state(AddQuestionStates.waiting_option_d)
    await message.answer("Enter <b>Option D</b>:", parse_mode="HTML")

@router.message(AddQuestionStates.waiting_option_d)
async def fsm_opt_d(message: Message, state: FSMContext):
    await state.update_data(option_d=message.text.strip())
    await state.set_state(AddQuestionStates.waiting_correct)
    await message.answer("Enter the <b>Correct Option (A, B, C, or D)</b>:", parse_mode="HTML")

@router.message(AddQuestionStates.waiting_correct)
async def fsm_opt_correct(message: Message, state: FSMContext):
    ans = message.text.strip().upper()
    if ans not in ("A", "B", "C", "D"):
        await message.reply("Invalid option! Please enter strictly A, B, C, or D:")
        return
    await state.update_data(correct_answer=ans)
    await state.set_state(AddQuestionStates.waiting_explanation)
    await message.answer("Enter optional <b>Explanation</b> (or send 'None'):", parse_mode="HTML")

@router.message(AddQuestionStates.waiting_explanation)
async def fsm_opt_exp(message: Message, state: FSMContext, db: Database):
    exp = message.text.strip()
    if exp.lower() in ("none", "yo'q", "-"):
        exp = None
    data = await state.get_data()
    await state.clear()

    q_data = [{
        "question": data["question_text"],
        "option_a": data["option_a"],
        "option_b": data["option_b"],
        "option_c": data["option_c"],
        "option_d": data["option_d"],
        "correct_answer": data["correct_answer"],
        "explanation": exp,
        "topic": "General",
        "difficulty": "Medium"
    }]

    async with db.get_connection() as conn:
        await queries.bulk_insert_questions(conn, data["quiz_id"], q_data)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Add Another Question", callback_data=f"adm:add_q:{data['quiz_id']}")],
        [InlineKeyboardButton(text="📋 Manage Quiz", callback_data=f"adm:quiz:{data['quiz_id']}")]
    ])
    await message.answer("✅ Question added successfully!", reply_markup=kb)

# ==========================================
# BULK QUESTION IMPORT
# ==========================================

@router.callback_query(F.data.startswith("adm:import:"))
async def cb_bulk_import_prompt(callback: CallbackQuery, state: FSMContext, is_admin: bool = False, lang: str = "uz"):
    if not is_admin:
        return
    quiz_id_str = callback.data.split(":")[2]
    quiz_id = int(quiz_id_str) if quiz_id_str.isdigit() and int(quiz_id_str) > 0 else None

    await state.set_state(ImportFileStates.waiting_file)
    await state.update_data(target_quiz_id=quiz_id)

    text = t("import_instructions", lang)
    await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()

@router.message(ImportFileStates.waiting_file, F.document)
async def handle_import_file_upload(message: Message, state: FSMContext, db: Database, lang: str = "uz"):
    doc = message.document
    filename = doc.file_name or "import.xlsx"
    ext = Path(filename).suffix.lower()

    if ext not in (".xlsx", ".xls", ".csv"):
        await message.reply("⚠️ Invalid file format! Please upload an <b>.xlsx</b> or <b>.csv</b> document.", parse_mode="HTML")
        return

    # Check file size (max 50 MB)
    if doc.file_size > config.MAX_FILE_SIZE_MB * 1024 * 1024:
        await message.reply(f"⚠️ File is too large! Maximum allowed size is {config.MAX_FILE_SIZE_MB}MB.")
        return

    status_msg = await message.answer(t("import_analyzing", lang))

    # Download file to imports directory
    dest_path = config.IMPORTS_DIR / f"{uuid.uuid4().hex[:8]}_{filename}"
    await message.bot.download(doc.file_id, destination=dest_path)

    # Parse and validate questions
    parsed = parse_import_file(dest_path, max_rows=config.MAX_IMPORT_ROWS)

    if parsed.valid_count == 0:
        err_text = "\n".join(f"• {e}" for e in parsed.errors[:10])
        await status_msg.edit_text(
            f"❌ <b>Import Failed! No valid questions found in file.</b>\n\n{err_text}",
            parse_mode="HTML"
        )
        await state.clear()
        if dest_path.exists():
            dest_path.unlink()
        return

    data = await state.get_data()
    target_quiz_id = data.get("target_quiz_id")

    # Store in memory registry for confirmation
    token = uuid.uuid4().hex[:12]
    _pending_imports[token] = {
        "file_path": dest_path,
        "valid_questions": parsed.valid_questions,
        "target_quiz_id": target_quiz_id,
        "filename": filename
    }

    error_preview = parsed.get_summary_text(max_errors=6)
    summary_text = t(
        "import_summary",
        lang,
        filename=escape_html(filename),
        total_rows=parsed.total_rows,
        valid_count=parsed.valid_count,
        invalid_count=parsed.invalid_count,
        duplicate_count=parsed.duplicate_count,
        duration=parsed.duration_seconds,
        error_preview=error_preview
    )

    kb = get_import_confirm_kb(token)
    await status_msg.edit_text(summary_text, reply_markup=kb, parse_mode="HTML")
    await state.clear()

@router.callback_query(F.data.startswith("imp:confirm:"))
async def cb_confirm_import(callback: CallbackQuery, db: Database, is_admin: bool = False, lang: str = "uz"):
    if not is_admin:
        return
    token = callback.data.split(":")[2]
    item = _pending_imports.pop(token, None)

    if not item:
        await callback.answer("Import session expired or already executed.", show_alert=True)
        return

    valid_questions = item["valid_questions"]
    target_quiz_id = item["target_quiz_id"]
    filename = item["filename"]

    async with db.get_connection() as conn:
        # If no target quiz was selected, create a new quiz automatically
        if not target_quiz_id:
            stem_title = Path(filename).stem.replace("_", " ").title()
            target_quiz_id = await queries.create_quiz(
                conn,
                title=f"Import: {stem_title}",
                description="Imported from spreadsheet",
                category="General",
                default_timer=30,
                shuffle_options=True,
                show_explanation=True,
                pass_percentage=60,
                is_published=True,
                created_by=callback.from_user.id
            )

        # Bulk insert
        count = await queries.bulk_insert_questions(conn, target_quiz_id, valid_questions)

    # Clean up file
    file_path: Path = item.get("file_path")
    if file_path and file_path.exists():
        try:
            file_path.unlink()
        except Exception:
            pass

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Manage This Quiz", callback_data=f"adm:quiz:{target_quiz_id}")],
        [InlineKeyboardButton(text="◀️ Admin Menu", callback_data="adm:menu")]
    ])
    await callback.message.edit_text(t("import_success", lang, count=count), reply_markup=kb, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data.startswith("imp:cancel:"))
async def cb_cancel_import(callback: CallbackQuery, is_admin: bool = False, lang: str = "uz"):
    if not is_admin:
        return
    token = callback.data.split(":")[2]
    item = _pending_imports.pop(token, None)
    if item:
        p: Path = item.get("file_path")
        if p and p.exists():
            try:
                p.unlink()
            except Exception:
                pass

    await callback.message.edit_text(t("import_cancelled", lang))
    await callback.answer()

# ==========================================
# TEMPLATES & EXPORT & BACKUP
# ==========================================

@router.callback_query(F.data == "adm:templates")
async def cb_download_templates(callback: CallbackQuery, is_admin: bool = False):
    if not is_admin:
        return
    await callback.answer("Generating templates...", show_alert=False)

    excel_path = config.TEMPLATES_DIR / "sample_questions.xlsx"
    csv_path = config.TEMPLATES_DIR / "sample_questions.csv"

    create_sample_excel_template(excel_path)
    create_sample_csv_template(csv_path)

    await callback.message.answer_document(
        document=FSInputFile(excel_path, filename="sample_questions.xlsx"),
        caption="📄 <b>Sample Excel Question Bank Template</b>\nFill in your questions and upload via 'Bulk Import'!",
        parse_mode="HTML"
    )
    await callback.message.answer_document(
        document=FSInputFile(csv_path, filename="sample_questions.csv"),
        caption="📄 <b>Sample CSV Question Bank Template (UTF-8)</b>",
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("adm:export:"))
async def cb_export_results(callback: CallbackQuery, db: Database, is_admin: bool = False):
    if not is_admin:
        return
    quiz_id = int(callback.data.split(":")[2])
    await callback.answer("Generating Excel export...", show_alert=False)

    async with db.get_connection() as conn:
        quiz = await queries.get_quiz(conn, quiz_id)
        results = await queries.get_all_results_for_export(conn, quiz_id)

    export_path = export_quiz_results_to_excel(
        quiz_title=quiz.title if quiz else f"Quiz_{quiz_id}",
        results=results,
        output_dir=config.EXPORTS_DIR
    )

    await callback.message.answer_document(
        document=FSInputFile(export_path, filename=export_path.name),
        caption=f"📊 <b>Results Export: {escape_html(quiz.title if quiz else '')}</b>\nTotal completed attempts: {len(results)}",
        parse_mode="HTML"
    )

@router.callback_query(F.data == "adm:backup")
async def cb_backup_db(callback: CallbackQuery, db: Database, is_admin: bool = False):
    if not is_admin:
        return
    await callback.answer("Creating hot SQLite backup...", show_alert=False)
    backup_file = await db.backup(config.BACKUP_DIR)

    await callback.message.answer_document(
        document=FSInputFile(backup_file, filename=backup_file.name),
        caption="💾 <b>SQLite Database Backup</b>\nSafely exported without locking active sessions.",
        parse_mode="HTML"
    )

# ==========================================
# USER MANAGEMENT & EXPORTS
# ==========================================

@router.callback_query(F.data.startswith("adm:users:"))
async def cb_admin_users(callback: CallbackQuery, db: Database, is_admin: bool = False, lang: str = "uz"):
    if not is_admin:
        await callback.answer(t("admin_not_authorized", lang), show_alert=True)
        return

    page = int(callback.data.split(":")[2])
    page_size = 8

    async with db.get_connection() as conn:
        users, total = await queries.list_users(conn, page=page, page_size=page_size)

    text = t("admin_users_title", lang, total=total)
    kb = get_admin_users_kb(users, page=page, total=total, page_size=page_size, lang=lang)

    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data.startswith("adm:user_view:") | (F.data.startswith("adm:user:") & ~F.data.startswith("adm:users:")))
async def cb_admin_user_view(callback: CallbackQuery, db: Database, is_admin: bool = False, lang: str = "uz"):
    if not is_admin:
        await callback.answer(t("admin_not_authorized", lang), show_alert=True)
        return

    try:
        user_id = int(callback.data.split(":")[2])
        async with db.get_connection() as conn:
            details = await queries.get_user_details(conn, user_id)

        if not details:
            await callback.answer("User not found.", show_alert=True)
            return

        tg_name = f"{details.get('first_name') or ''} {details.get('last_name') or ''}".strip() or "Anonymous"
        username = f"(@{details['username']})" if details.get('username') else ""
        real_name = details.get("real_name") or ("Kiritilmagan" if lang == "uz" else "Not set")
        student_group = details.get("student_group") or ("Kiritilmagan" if lang == "uz" else "Not set")
        phone = details.get("phone_number") or ("Kiritilmagan" if lang == "uz" else "Not set")
        avg_score = round(details.get("avg_score") or 0.0, 1)
        last_act = details.get("last_active") or details.get("created_at") or "-"

        text = t(
            "admin_user_detail",
            lang,
            telegram_id=details["telegram_id"],
            tg_name=escape_html(tg_name),
            username=escape_html(username),
            real_name=escape_html(real_name),
            student_group=escape_html(student_group),
            phone_number=escape_html(phone),
            user_lang=details.get("language_code", "uz"),
            created_at=details.get("created_at", "-"),
            total_attempts=details.get("total_attempts", 0),
            passed_count=details.get("passed_count", 0),
            avg_score=avg_score,
            last_active=last_act
        )

        is_target_admin = config.is_admin(user_id)
        kb = get_admin_user_detail_kb(user_id, is_target_admin=is_target_admin, lang=lang)
        try:
            await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
        except Exception:
            await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Error in cb_admin_user_view: {e}", exc_info=True)
        await callback.answer(f"Error: {e}", show_alert=True)
    finally:
        try:
            await callback.answer()
        except Exception:
            pass

@router.callback_query(F.data.startswith("adm:del_user_conf:"))
async def cb_admin_del_user_conf(callback: CallbackQuery, db: Database, is_admin: bool = False, lang: str = "uz"):
    if not is_admin:
        await callback.answer(t("admin_not_authorized", lang), show_alert=True)
        return

    user_id = int(callback.data.split(":")[2])
    if config.is_admin(user_id):
        await callback.answer(t("admin_cannot_delete_admin", lang), show_alert=True)
        return

    async with db.get_connection() as conn:
        user = await queries.get_user(conn, user_id)

    if not user:
        await callback.answer("User not found.", show_alert=True)
        return

    name = user.real_name or f"{user.first_name or ''} {user.last_name or ''}".strip() or (f"@{user.username}" if user.username else f"User {user.telegram_id}")
    text = t("admin_delete_user_confirm", lang, name=escape_html(name), user_id=user.telegram_id)
    kb = get_admin_user_delete_confirm_kb(user_id, lang=lang)

    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data.startswith("adm:del_user_do:"))
async def cb_admin_del_user_do(callback: CallbackQuery, db: Database, is_admin: bool = False, lang: str = "uz"):
    if not is_admin:
        await callback.answer(t("admin_not_authorized", lang), show_alert=True)
        return

    user_id = int(callback.data.split(":")[2])
    if config.is_admin(user_id):
        await callback.answer(t("admin_cannot_delete_admin", lang), show_alert=True)
        return

    async with db.get_connection() as conn:
        await queries.delete_user(conn, user_id)
        users, total = await queries.list_users(conn, page=0, page_size=8)

    await callback.answer(t("admin_user_deleted", lang), show_alert=True)

    text = t("admin_users_title", lang, total=total)
    kb = get_admin_users_kb(users, page=0, total=total, page_size=8, lang=lang)

    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data == "adm:clear_users_conf")
async def cb_admin_clear_users_conf(callback: CallbackQuery, is_admin: bool = False, lang: str = "uz"):
    if not is_admin:
        await callback.answer(t("admin_not_authorized", lang), show_alert=True)
        return

    text = t("admin_clear_users_confirm", lang)
    kb = get_admin_clear_users_confirm_kb(lang=lang)

    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "adm:clear_users_do")
async def cb_admin_clear_users_do(callback: CallbackQuery, db: Database, is_admin: bool = False, lang: str = "uz"):
    if not is_admin:
        await callback.answer(t("admin_not_authorized", lang), show_alert=True)
        return

    async with db.get_connection() as conn:
        count = await queries.clear_all_non_admin_users(conn)
        users, total = await queries.list_users(conn, page=0, page_size=8)

    await callback.answer(t("admin_users_cleared", lang, count=count), show_alert=True)

    text = t("admin_users_title", lang, total=total)
    kb = get_admin_users_kb(users, page=0, total=total, page_size=8, lang=lang)

    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data == "adm:export_users")
async def cb_admin_export_users(callback: CallbackQuery, db: Database, is_admin: bool = False, lang: str = "uz"):
    if not is_admin:
        await callback.answer(t("admin_not_authorized", lang), show_alert=True)
        return

    await callback.answer("Generating Excel report...", show_alert=False)

    async with db.get_connection() as conn:
        users_data = await queries.get_all_users_export_data(conn)

    export_path = export_all_users_to_excel(users_data, output_dir=config.EXPORTS_DIR)

    caption = (
        f"📊 <b>Foydalanuvchilar va imtihon statistikasi hisoboti</b>\n"
        f"Jami foydalanuvchilar: <b>{len(users_data)}</b> ta"
        if lang == "uz" else
        f"📊 <b>Users & Exam Statistics Report</b>\n"
        f"Total users: <b>{len(users_data)}</b>"
    )

    await callback.message.answer_document(
        document=FSInputFile(export_path, filename=export_path.name),
        caption=caption,
        parse_mode="HTML"
    )
