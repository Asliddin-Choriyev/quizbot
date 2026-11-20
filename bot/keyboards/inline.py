import random
from typing import List, Optional
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.utils.i18n import t
from bot.database.models import QuestionOption, Quiz

# ==========================================
# COMMON KEYBOARDS
# ==========================================

def get_main_menu_kb(lang: str = "uz", is_admin: bool = False) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text=t("btn_browse_quizzes", lang), callback_data="quizzes:list:0"),
            InlineKeyboardButton(text=t("btn_my_results", lang), callback_data="user:results")
        ],
        [
            InlineKeyboardButton(text=t("btn_my_profile", lang), callback_data="user:profile"),
            InlineKeyboardButton(text="🌐 Til / Language", callback_data="user:language")
        ]
    ]
    if is_admin:
        buttons.append([
            InlineKeyboardButton(text=t("btn_admin_panel", lang), callback_data="adm:menu")
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_profile_kb(lang: str = "uz") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=t("btn_edit_profile", lang), callback_data="user:edit_profile"),
                InlineKeyboardButton(text=t("btn_my_results", lang), callback_data="user:results")
            ],
            [
                InlineKeyboardButton(text=t("btn_back", lang), callback_data="main:menu")
            ]
        ]
    )

def get_language_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang:uz"),
                InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:en")
            ],
            [
                InlineKeyboardButton(text="◀️ Orqaga / Back", callback_data="main:menu")
            ]
        ]
    )

# ==========================================
# QUIZ BROWSER & LANDING KEYBOARDS
# ==========================================

def get_quiz_list_kb(quizzes: List[Quiz], page: int = 0, total_count: int = 0, page_size: int = 6, lang: str = "uz") -> InlineKeyboardMarkup:
    rows = []
    for q in quizzes:
        if "ta savol" in q.title or "Qs" in q.title:
            title = q.title
        else:
            q_label = "ta savol" if lang == "uz" else "Qs"
            title = f"{q.title} ({q.question_count} {q_label})"
        rows.append([InlineKeyboardButton(text=title, callback_data=f"quiz:view:{q.id}")])

    # Pagination buttons
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="◀️ Prev", callback_data=f"quizzes:list:{page - 1}"))
    if (page + 1) * page_size < total_count:
        nav_buttons.append(InlineKeyboardButton(text="Next ▶️", callback_data=f"quizzes:list:{page + 1}"))

    if nav_buttons:
        rows.append(nav_buttons)

    rows.append([InlineKeyboardButton(text=t("btn_back", lang), callback_data="main:menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_quiz_landing_kb(quiz_id: int, bot_username: str, lang: str = "uz") -> InlineKeyboardMarkup:
    bot_name = bot_username or "quizzes_makerbot"
    group_link = f"https://t.me/{bot_name}?startgroup=quiz_{quiz_id}"

    start_text = t("btn_start_quiz", lang)
    group_text = t("btn_start_in_group", lang)
    share_text = t("btn_share_quiz", lang)

    rows = [
        [
            InlineKeyboardButton(text=start_text, callback_data=f"quiz:start:{quiz_id}")
        ],
        [
            InlineKeyboardButton(text=group_text, url=group_link)
        ],
        [
            InlineKeyboardButton(text=share_text, switch_inline_query=str(quiz_id))
        ],
        [
            InlineKeyboardButton(text=t("btn_leaderboard", lang), callback_data=f"quiz:leaderboard:{quiz_id}"),
            InlineKeyboardButton(text=t("btn_back", lang), callback_data="quizzes:list:0")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)

# ==========================================
# QUIZ TAKING KEYBOARDS
# ==========================================

def get_question_options_kb(
    session_code: str,
    question_id: int,
    options: List[QuestionOption],
    shuffle: bool = True
) -> InlineKeyboardMarkup:
    opts = list(options)
    if shuffle:
        random.shuffle(opts)

    rows = []
    for opt in opts:
        btn_text = f"{opt.option_label}) {opt.option_text}"
        # Keep button label clean and readable
        if len(btn_text) > 40:
            btn_text = btn_text[:37] + "..."
        rows.append([
            InlineKeyboardButton(
                text=btn_text,
                callback_data=f"ans:{session_code}:{question_id}:{opt.option_label}"
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_quiz_completed_kb(session_id: int, quiz_id: int, has_mistakes: bool = True, lang: str = "uz") -> InlineKeyboardMarkup:
    rows = []
    if has_mistakes:
        rows.append([
            InlineKeyboardButton(text=t("btn_review_mistakes", lang), callback_data=f"sess:review:{session_id}")
        ])
    rows.append([
        InlineKeyboardButton(text=t("btn_retry_quiz", lang), callback_data=f"quiz:start:{quiz_id}"),
        InlineKeyboardButton(text=t("btn_leaderboard", lang), callback_data=f"quiz:leaderboard:{quiz_id}")
    ])
    rows.append([
        InlineKeyboardButton(text=t("btn_browse_quizzes", lang), callback_data="quizzes:list:0")
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_quiz_paused_kb(session_id: int, lang: str = "uz") -> InlineKeyboardMarkup:
    resume_text = "▶️ Testni davom ettirish" if lang == "uz" else "▶️ Resume Quiz"
    finish_text = "⏹ Testni yakunlash" if lang == "uz" else "⏹ Finish Quiz"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=resume_text, callback_data=f"quiz:resume:{session_id}")
            ],
            [
                InlineKeyboardButton(text=finish_text, callback_data=f"quiz:finish:{session_id}")
            ]
        ]
    )

# ==========================================
# GROUP COMPETITION KEYBOARDS
# ==========================================

def get_group_lobby_kb(comp_id: int, lang: str = "uz") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=t("btn_join_group", lang), callback_data=f"gjoin:{comp_id}")
            ],
            [
                InlineKeyboardButton(text=t("btn_start_group_now", lang), callback_data=f"gstart:{comp_id}")
            ]
        ]
    )

def get_group_question_kb(comp_id: int, question_id: int, options: List[QuestionOption]) -> InlineKeyboardMarkup:
    rows = []
    # Grid of 2x2 or 4 rows
    for opt in options:
        btn_text = f"{opt.option_label}) {opt.option_text}"
        if len(btn_text) > 35:
            btn_text = btn_text[:32] + "..."
        rows.append([
            InlineKeyboardButton(text=btn_text, callback_data=f"gans:{comp_id}:{question_id}:{opt.option_label}")
        ])
    return InlineKeyboardMarkup(inline_keyboard=rows)

# ==========================================
# ADMIN PANEL KEYBOARDS
# ==========================================

def get_admin_menu_kb(lang: str = "uz") -> InlineKeyboardMarkup:
    users_btn = "👥 Foydalanuvchilar" if lang == "uz" else "👥 Users"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=t("btn_admin_quizzes", lang), callback_data="adm:quizzes:0"),
                InlineKeyboardButton(text=t("btn_admin_create_quiz", lang), callback_data="adm:create_quiz")
            ],
            [
                InlineKeyboardButton(text=t("btn_admin_import", lang), callback_data="adm:import:0"),
                InlineKeyboardButton(text=t("btn_admin_templates", lang), callback_data="adm:templates")
            ],
            [
                InlineKeyboardButton(text=users_btn, callback_data="adm:users:0"),
                InlineKeyboardButton(text=t("btn_admin_backup", lang), callback_data="adm:backup")
            ],
            [
                InlineKeyboardButton(text="◀️ Main Menu", callback_data="main:menu")
            ]
        ]
    )

def get_admin_users_kb(users: list, page: int = 0, total: int = 0, page_size: int = 8, lang: str = "uz") -> InlineKeyboardMarkup:
    rows = []
    for u in users:
        real = u.get("real_name")
        tg_name = f"{u.get('first_name') or ''} {u.get('last_name') or ''}".strip()
        name = real or tg_name or (f"@{u['username']}" if u.get('username') else f"ID: {u['telegram_id']}")
        attempts = u.get("total_attempts", 0)
        avg = f"{round(u.get('avg_score', 0), 1)}%" if u.get("avg_score") else "0%"
        btn_text = f"👤 {name} ({attempts} test | {avg})"
        if len(btn_text) > 38:
            btn_text = btn_text[:35] + "..."
        rows.append([InlineKeyboardButton(text=btn_text, callback_data=f"adm:user_view:{u['telegram_id']}")])

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="◀️ Prev", callback_data=f"adm:users:{page - 1}"))
    if (page + 1) * page_size < total:
        nav.append(InlineKeyboardButton(text="Next ▶️", callback_data=f"adm:users:{page + 1}"))
    if nav:
        rows.append(nav)

    export_btn = "📥 Barchasini Excelga yuklash" if lang == "uz" else "📥 Export All to Excel"
    rows.append([InlineKeyboardButton(text=export_btn, callback_data="adm:export_users")])
    if total > 0:
        clear_btn = "🗑 Barcha foydalanuvchilarni tozalash" if lang == "uz" else "🗑 Clear All Users"
        rows.append([InlineKeyboardButton(text=clear_btn, callback_data="adm:clear_users_conf")])
    rows.append([InlineKeyboardButton(text="◀️ Admin Menu", callback_data="adm:menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_admin_clear_users_confirm_kb(lang: str = "uz") -> InlineKeyboardMarkup:
    yes_btn = "🗑 Ha, barchasini tozalash" if lang == "uz" else "🗑 Yes, clear all"
    cancel_btn = t("btn_cancel", lang)
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=yes_btn, callback_data="adm:clear_users_do"),
                InlineKeyboardButton(text=cancel_btn, callback_data="adm:users:0")
            ]
        ]
    )

def get_admin_user_detail_kb(user_id: int, is_target_admin: bool = False, lang: str = "uz") -> InlineKeyboardMarkup:
    del_btn = "🗑 Foydalanuvchini o'chirish" if lang == "uz" else "🗑 Delete User"
    back_btn = "◀️ Foydalanuvchilar ro'yxati" if lang == "uz" else "◀️ Users List"
    buttons = []
    if not is_target_admin:
        buttons.append([InlineKeyboardButton(text=del_btn, callback_data=f"adm:del_user_conf:{user_id}")])
    buttons.append([InlineKeyboardButton(text=back_btn, callback_data="adm:users:0")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_admin_user_delete_confirm_kb(user_id: int, lang: str = "uz") -> InlineKeyboardMarkup:
    yes_btn = "🗑 Ha, o'chirilsin" if lang == "uz" else "🗑 Yes, delete"
    cancel_btn = t("btn_cancel", lang)
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=yes_btn, callback_data=f"adm:del_user_do:{user_id}"),
                InlineKeyboardButton(text=cancel_btn, callback_data=f"adm:user_view:{user_id}")
            ]
        ]
    )

def get_admin_quizzes_kb(quizzes: List[Quiz], page: int = 0, total: int = 0, page_size: int = 6) -> InlineKeyboardMarkup:
    rows = []
    for q in quizzes:
        pub_icon = "🟢" if q.is_published else "🔴"
        title = f"{pub_icon} {q.title} ({q.question_count} Qs)"
        rows.append([InlineKeyboardButton(text=title, callback_data=f"adm:quiz:{q.id}")])

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="◀️ Prev", callback_data=f"adm:quizzes:{page - 1}"))
    if (page + 1) * page_size < total:
        nav.append(InlineKeyboardButton(text="Next ▶️", callback_data=f"adm:quizzes:{page + 1}"))
    if nav:
        rows.append(nav)

    rows.append([
        InlineKeyboardButton(text="➕ New Quiz", callback_data="adm:create_quiz"),
        InlineKeyboardButton(text="◀️ Admin Menu", callback_data="adm:menu")
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_admin_quiz_manage_kb(quiz: Quiz, lang: str = "uz") -> InlineKeyboardMarkup:
    pub_text = "🔴 Unpublish" if quiz.is_published else "🟢 Publish"
    shuf_text = f"🔀 Shuffling: {'ON' if quiz.shuffle_options else 'OFF'}"
    exp_text = f"💡 Explanations: {'ON' if quiz.show_explanation else 'OFF'}"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👁 Preview Questions", callback_data=f"adm:preview:{quiz.id}:0"),
                InlineKeyboardButton(text="➕ Add Question", callback_data=f"adm:add_q:{quiz.id}")
            ],
            [
                InlineKeyboardButton(text="📥 Import Questions (.xlsx/.csv)", callback_data=f"adm:import:{quiz.id}"),
                InlineKeyboardButton(text="📊 Export Excel", callback_data=f"adm:export:{quiz.id}")
            ],
            [
                InlineKeyboardButton(text=f"⏱ Timer: {quiz.default_timer}s", callback_data=f"adm:settimer:{quiz.id}"),
                InlineKeyboardButton(text=f"🎯 Pass: {quiz.pass_percentage}%", callback_data=f"adm:setpass:{quiz.id}")
            ],
            [
                InlineKeyboardButton(text=shuf_text, callback_data=f"adm:togshuf:{quiz.id}"),
                InlineKeyboardButton(text=exp_text, callback_data=f"adm:togexp:{quiz.id}")
            ],
            [
                InlineKeyboardButton(text=pub_text, callback_data=f"adm:togpub:{quiz.id}"),
                InlineKeyboardButton(text="🗑 Delete Quiz", callback_data=f"adm:delconf:{quiz.id}")
            ],
            [
                InlineKeyboardButton(text="◀️ Quizzes List", callback_data="adm:quizzes:0")
            ]
        ]
    )

def get_admin_timer_options_kb(quiz_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="10s", callback_data=f"adm:savetimer:{quiz_id}:10"),
                InlineKeyboardButton(text="15s", callback_data=f"adm:savetimer:{quiz_id}:15"),
                InlineKeyboardButton(text="20s", callback_data=f"adm:savetimer:{quiz_id}:20")
            ],
            [
                InlineKeyboardButton(text="30s", callback_data=f"adm:savetimer:{quiz_id}:30"),
                InlineKeyboardButton(text="45s", callback_data=f"adm:savetimer:{quiz_id}:45"),
                InlineKeyboardButton(text="60s", callback_data=f"adm:savetimer:{quiz_id}:60")
            ],
            [
                InlineKeyboardButton(text="Custom Duration", callback_data=f"adm:customtimer:{quiz_id}"),
                InlineKeyboardButton(text="◀️ Back", callback_data=f"adm:quiz:{quiz_id}")
            ]
        ]
    )

def get_admin_pass_mark_options_kb(quiz_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="50%", callback_data=f"adm:savepass:{quiz_id}:50"),
                InlineKeyboardButton(text="60%", callback_data=f"adm:savepass:{quiz_id}:60"),
                InlineKeyboardButton(text="70%", callback_data=f"adm:savepass:{quiz_id}:70")
            ],
            [
                InlineKeyboardButton(text="80%", callback_data=f"adm:savepass:{quiz_id}:80"),
                InlineKeyboardButton(text="90%", callback_data=f"adm:savepass:{quiz_id}:90"),
                InlineKeyboardButton(text="100%", callback_data=f"adm:savepass:{quiz_id}:100")
            ],
            [
                InlineKeyboardButton(text="◀️ Back", callback_data=f"adm:quiz:{quiz_id}")
            ]
        ]
    )

def get_admin_delete_confirm_kb(quiz_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⚠️ YES, DELETE QUIZ", callback_data=f"adm:delquiz:{quiz_id}")
            ],
            [
                InlineKeyboardButton(text="❌ Cancel", callback_data=f"adm:quiz:{quiz_id}")
            ]
        ]
    )

def get_import_confirm_kb(import_token: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Confirm & Import", callback_data=f"imp:confirm:{import_token}"),
                InlineKeyboardButton(text="❌ Cancel", callback_data=f"imp:cancel:{import_token}")
            ]
        ]
    )
