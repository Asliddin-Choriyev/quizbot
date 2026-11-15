from typing import Dict, Any

TRANSLATIONS: Dict[str, Dict[str, str]] = {
    # ------------------ Common ------------------
    "welcome_title": {
        "en": "👋 <b>Welcome to QuizBot!</b>\n\nI am an advanced examination and quiz bot. You can test your knowledge individually or compete with your friends in group chats!",
        "uz": "👋 <b>QuizBot-ga xush kelibsiz!</b>\n\nMen zamonaviy test va viktorina botiman. Siz mustaqil ravishda bilimingizni sinashingiz yoki guruhlarda do'stlaringiz bilan bellashishingiz mumkin!"
    },
    "help_text": {
        "en": "📚 <b>QuizBot Commands:</b>\n\n/start - Start the bot or open a quiz\n/quizzes - Browse all available quizzes\n/myresults - View your past quiz results\n/language - Change interface language\n/admin - Open Admin Control Panel (Admins only)",
        "uz": "📚 <b>QuizBot Buyruqlari:</b>\n\n/start - Botni ishga tushirish yoki viktorinani ochish\n/quizzes - Barcha mavjud testlar ro'yxati\n/myresults - Natijalaringiz tarixi\n/language - Tilni o'zgartirish\n/admin - Administrator paneli (faqat adminlar uchun)"
    },
    "choose_language": {
        "en": "🌐 <b>Select your interface language:</b>",
        "uz": "🌐 <b>Interfeys tilini tanlang:</b>"
    },
    "language_changed": {
        "en": "✅ Language successfully set to English!",
        "uz": "✅ Til muvaffaqiyatli O'zbek tiliga o'zgartirildi!"
    },
    "btn_browse_quizzes": {
        "en": "📚 Browse Quizzes",
        "uz": "📚 Testlar ro'yxati"
    },
    "btn_my_results": {
        "en": "📊 My Results",
        "uz": "📊 Natijalarim"
    },
    "btn_my_profile": {
        "en": "👤 My Profile",
        "uz": "👤 Profilim"
    },
    "btn_edit_profile": {
        "en": "✏️ Edit Profile",
        "uz": "✏️ Profilni tahrirlash"
    },
    "profile_info": {
        "en": "👤 <b>My Profile</b>\n\n🆔 Telegram ID: <code>{telegram_id}</code>\n👤 Telegram: {tg_name} {username}\n📝 Full Name: <b>{real_name}</b>\n🎓 Group / Faculty: <b>{student_group}</b>\n📱 Phone: <b>{phone_number}</b>\n\n📊 <b>Performance Stats:</b>\n• Total Quizzes: <b>{total_attempts}</b>\n• Passed Quizzes: <b>{passed_count}</b>\n• Average Score: <b>{avg_score}%</b>\n• Correct Answers: <b>{total_correct}</b>\n• Total Time: <b>{total_duration}</b>",
        "uz": "👤 <b>Mening Profilim</b>\n\n🆔 Telegram ID: <code>{telegram_id}</code>\n👤 Telegram: {tg_name} {username}\n📝 F.I.SH.: <b>{real_name}</b>\n🎓 Guruh / Fakultet: <b>{student_group}</b>\n📱 Telefon: <b>{phone_number}</b>\n\n📊 <b>Natijalar statistikasi:</b>\n• Jami topshirilgan testlar: <b>{total_attempts}</b> ta\n• Muvaffaqiyatli testlar: <b>{passed_count}</b> ta\n• O'rtacha natija: <b>{avg_score}%</b>\n• To'g'ri javoblar: <b>{total_correct}</b> ta\n• Umumiy sarflangan vaqt: <b>{total_duration}</b>"
    },
    "profile_prompt_name": {
        "en": "📝 Please enter your <b>Full Name (First & Last name)</b>:\n\n<i>Example: John Doe</i>",
        "uz": "📝 Iltimos, haqiqiy <b>Ism va Familiyangizni (F.I.SH.)</b> kiriting:\n\n<i>Misol: Aliyev Vali</i>"
    },
    "profile_prompt_group": {
        "en": "🎓 Enter your <b>Student Group or Faculty</b>:\n\n<i>Example: 201-group, Medicine</i>\n<i>(Press '⏭ Skip' if you don't want to specify)</i>",
        "uz": "🎓 <b>Guruhingiz yoki fakultetingizni</b> kiriting:\n\n<i>Misol: 201-guruh, Davolash</i>\n<i>(Kiritishni xohlamasangiz, '⏭ O'tkazib yuborish' tugmasini bosing)</i>"
    },
    "profile_prompt_phone": {
        "en": "📱 Send your <b>Phone Number</b> or click the button below:\n\n<i>(Press '⏭ Skip' if you don't want to specify)</i>",
        "uz": "📱 <b>Telefon raqamingizni</b> yuboring yoki quyidagi tugmani bosing:\n\n<i>(Kiritishni xohlamasangiz, '⏭ O'tkazib yuborish' tugmasini bosing)</i>"
    },
    "profile_updated_success": {
        "en": "✅ <b>Your profile has been updated successfully!</b>",
        "uz": "✅ <b>Profilingiz muvaffaqiyatli yangilandi!</b>"
    },
    "profile_edit_cancelled": {
        "en": "❌ Profile editing was cancelled.",
        "uz": "❌ Profilni tahrirlash bekor qilindi."
    },
    "btn_admin_panel": {
        "en": "⚙️ Admin Panel",
        "uz": "⚙️ Admin Panel"
    },
    "btn_cancel": {
        "en": "❌ Cancel",
        "uz": "❌ Bekor qilish"
    },
    "btn_back": {
        "en": "◀️ Back",
        "uz": "◀️ Orqaga"
    },
    "btn_next": {
        "en": "Next ➡️",
        "uz": "Keyingisi ➡️"
    },
    
    # ------------------ Student & Quiz Landing ------------------
    "quiz_list_title": {
        "en": "📋 <b>Available Quizzes</b>\nChoose a quiz to start testing your knowledge:",
        "uz": "📋 <b>Mavjud Testlar</b>\nBilimingizni sinash uchun testni tanlang:"
    },
    "no_quizzes_available": {
        "en": "ℹ️ There are currently no published quizzes available.",
        "uz": "ℹ️ Hozircha e'lon qilingan testlar mavjud emas."
    },
    "quiz_landing": {
        "en": "🎲 <b>“{title}”</b>\n{description}\n\n🖋 <i>{question_count} questions · ⏱ {timer} seconds</i>",
        "uz": "🎲 <b>“{title}”</b>\n{description}\n\n🖋 <i>{question_count} ta savol · ⏱ {timer} soniya</i>"
    },
    "btn_start_quiz": {
        "en": "Start this quiz",
        "uz": "Bu testni boshlash"
    },
    "btn_start_in_group": {
        "en": "Start in Group",
        "uz": "Guruhda testni boshlash"
    },
    "btn_share_quiz": {
        "en": "Share quiz",
        "uz": "Testni ulashish"
    },
    "btn_leaderboard": {
        "en": "🏆 Leaderboard",
        "uz": "🏆 Natijalar jadvali"
    },
    "share_text": {
        "en": "Check out this quiz: \"{title}\" on QuizBot! Test your knowledge now:",
        "uz": "QuizBot-da ushbu testni topshirib ko'ring: \"{title}\"!"
    },
    "enabled": {"en": "Yes", "uz": "Ha"},
    "disabled": {"en": "No", "uz": "Yo'q"},

    # ------------------ Quiz Taking ------------------
    "question_header": {
        "en": "❓ <b>Question {index} of {total}</b>  |  ⏱ <b>{timer}s</b>\n📁 <i>{topic}</i>\n{progress_bar}\n\n<b>{text}</b>",
        "uz": "❓ <b>{index}-savol / {total}</b>  |  ⏱ <b>{timer} soniya</b>\n📁 <i>{topic}</i>\n{progress_bar}\n\n<b>{text}</b>"
    },
    "toast_correct": {
        "en": "✅ Correct! Well done!",
        "uz": "✅ To'g'ri javob! Barakalla!"
    },
    "toast_incorrect": {
        "en": "❌ Incorrect answer!",
        "uz": "❌ Noto'g'ri javob!"
    },
    "toast_already_answered": {
        "en": "⚠️ You have already answered this question!",
        "uz": "⚠️ Siz bu savolga allaqachon javob bergansiz!"
    },
    "time_expired": {
        "en": "⏰ <b>Time expired!</b> Moving to the next question...",
        "uz": "⏰ <b>Vaqt tugadi!</b> Keyingi savolga o'tilmoqda..."
    },
    "explanation_header": {
        "en": "\n\n💡 <b>Explanation:</b> {explanation}",
        "uz": "\n\n💡 <b>Izoh:</b> {explanation}"
    },
    "quiz_completed_title": {
        "en": "🏁 <b>Quiz Completed!</b>\n\nQuiz: <b>{title}</b>\n\n{status_badge}\n\n📊 <b>Total questions:</b> {total}\n✅ <b>Correct:</b> {correct} ({score_pct}%)\n❌ <b>Incorrect:</b> {incorrect}\n⏳ <b>Unanswered:</b> {unanswered}\n⏱ <b>Total time:</b> {duration}\n🎯 <b>Passing threshold:</b> {pass_threshold}%",
        "uz": "🏁 <b>Test Yakunlandi!</b>\n\nTest: <b>{title}</b>\n\n{status_badge}\n\n📊 <b>Jami savollar:</b> {total}\n✅ <b>To'g'ri:</b> {correct} ({score_pct}%)\n❌ <b>Noto'g'ri:</b> {incorrect}\n⏳ <b>Javobsiz:</b> {unanswered}\n⏱ <b>Sarflangan vaqt:</b> {duration}\n🎯 <b>O'tish chegarasi:</b> {pass_threshold}%"
    },
    "passed_badge": {
        "en": "🎉 <b>STATUS: PASSED!</b> Congratulations!",
        "uz": "🎉 <b>NATIJA: MUVAFFAQIYATLI O'TDINGIZ!</b> Tabriklaymiz!"
    },
    "failed_badge": {
        "en": "😔 <b>STATUS: NOT PASSED.</b> Try again to improve your score!",
        "uz": "😔 <b>NATIJA: O'TA OLMADINGIZ.</b> Natijangizni yaxshilash uchun qayta urinib ko'ring!"
    },
    "btn_review_mistakes": {
        "en": "🔍 Review Incorrect Answers",
        "uz": "🔍 Xatolarni ko'rib chiqish"
    },
    "btn_retry_quiz": {
        "en": "🔄 Try Again",
        "uz": "🔄 Qayta topshirish"
    },
    "no_mistakes": {
        "en": "🎉 Perfect score! You made zero mistakes.",
        "uz": "🎉 A'lo natija! Siz birorta ham xato qilmadingiz."
    },
    "review_item": {
        "en": "<b>Question:</b> {question}\n❌ <b>Your answer:</b> {your_ans}\n✅ <b>Correct answer:</b> {correct_ans}\n💡 <b>Explanation:</b> {explanation}\n",
        "uz": "<b>Savol:</b> {question}\n❌ <b>Sizning javobingiz:</b> {your_ans}\n✅ <b>To'g'ri javob:</b> {correct_ans}\n💡 <b>Izoh:</b> {explanation}\n"
    },

    # ------------------ Group Competition ------------------
    "group_lobby_title": {
        "en": "👥 <b>Group Quiz Competition: {title}</b>\n\n📝 {description}\n❓ <b>Questions:</b> {question_count}\n⏱ <b>Time per question:</b> {timer}s\n\nClick <b>\"Join Competition\"</b> below to participate!\nThe quiz starts when the host clicks <b>\"Start Now\"</b>.",
        "uz": "👥 <b>Guruhli Viktorina: {title}</b>\n\n📝 {description}\n❓ <b>Savollar soni:</b> {question_count}\n⏱ <b>Har bir savol vaqti:</b> {timer} soniya\n\nQatnashish uchun quyidagi <b>\"Qo'shilish\"</b> tugmasini bosing!\nBoshlovchi <b>\"Hozir boshlash\"</b> tugmasini bosganda test boshlanadi."
    },
    "btn_join_group": {
        "en": "🙋‍♂️ Join Competition",
        "uz": "🙋‍♂️ Qo'shilish"
    },
    "btn_start_group_now": {
        "en": "🚀 Start Now",
        "uz": "🚀 Hozir boshlash"
    },
    "joined_competition": {
        "en": "✅ You joined the competition!",
        "uz": "✅ Siz musobaqaga qo'shildingiz!"
    },
    "group_question_header": {
        "en": "👥 <b>Group Quiz: {quiz_title}</b>\n❓ <b>Question {index} of {total}</b> | ⏱ <b>{timer}s</b>\n\n<b>{text}</b>",
        "uz": "👥 <b>Guruhli Test: {quiz_title}</b>\n❓ <b>{index}-savol / {total}</b> | ⏱ <b>{timer} soniya</b>\n\n<b>{text}</b>"
    },
    "group_round_end": {
        "en": "⏱ <b>Round over!</b>\n✅ Correct answer: <b>{correct_option}</b>\n{explanation}\n\n📊 <b>Current Top Participants:</b>\n{leaderboard}",
        "uz": "⏱ <b>Raund tugadi!</b>\n✅ To'g'ri javob: <b>{correct_option}</b>\n{explanation}\n\n📊 <b>Hozirgi yetakchilar:</b>\n{leaderboard}"
    },
    "group_final_leaderboard": {
        "en": "🏆 <b>GROUP COMPETITION FINISHED!</b>\n\nQuiz: <b>{title}</b>\nQuestions: {total}\n\n🏅 <b>FINAL LEADERBOARD:</b>\n{leaderboard}\n\n👏 Thank you everyone for participating!",
        "uz": "🏆 <b>GURUH MUSOBAQASI YAKUNLANDI!</b>\n\nTest: <b>{title}</b>\nSavollar: {total}\n\n🏅 <b>YAKUNIY NATIJALAR:</b>\n{leaderboard}\n\n👏 Barcha ishtirokchilarga tashakkur!"
    },
    "not_group_creator": {
        "en": "⚠️ Only the user who started the lobby or group admins can start this competition.",
        "uz": "⚠️ Faqat musobaqani yaratgan foydalanuvchi yoki guruh admini boshlashi mumkin."
    },

    # ------------------ Admin Panel ------------------
    "admin_welcome": {
        "en": "⚙️ <b>Admin Control Panel</b>\n\n📊 <b>System Statistics:</b>\n• Total Quizzes: <b>{quiz_count}</b>\n• Total Questions: <b>{question_count}</b>\n• Registered Users: <b>{user_count}</b>\n\nChoose an action from the menu below:",
        "uz": "⚙️ <b>Administrator Boshqaruv Paneli</b>\n\n📊 <b>Tizim Statistikasi:</b>\n• Jami testlar: <b>{quiz_count}</b>\n• Jami savollar: <b>{question_count}</b>\n• Foydalanuvchilar: <b>{user_count}</b>\n\nQuyidagi menyudan kerakli amalni tanlang:"
    },
    "admin_not_authorized": {
        "en": "⛔ Access denied. You do not have administrator permissions.",
        "uz": "⛔ Ruxsat berilmadi. Sizda administrator huquqlari yo'q."
    },
    "admin_users_title": {
        "en": "👥 <b>Registered Users ({total} total)</b>\nSelect a user to view full profile & performance:",
        "uz": "👥 <b>Ro'yxatdan O'tgan Foydalanuvchilar ({total} ta)</b>\nBatafsil ma'lumot va natijalarini ko'rish uchun foydalanuvchini tanlang:"
    },
    "admin_user_detail": {
        "en": "👤 <b>User Details</b>\n\n🆔 User ID: <code>{telegram_id}</code>\n👤 Telegram: {tg_name} {username}\n📝 Full Name: <b>{real_name}</b>\n🎓 Group: <b>{student_group}</b>\n📱 Phone: <b>{phone_number}</b>\n🌐 Language: <b>{user_lang}</b>\n📅 Joined: <b>{created_at}</b>\n\n📊 <b>Exam Statistics:</b>\n• Total Tests Taken: <b>{total_attempts}</b>\n• Passed Tests: <b>{passed_count}</b>\n• Average Score: <b>{avg_score}%</b>\n• Last Active: <b>{last_active}</b>",
        "uz": "👤 <b>Foydalanuvchi Ma'lumotlari</b>\n\n🆔 Foydalanuvchi ID: <code>{telegram_id}</code>\n👤 Telegram: {tg_name} {username}\n📝 F.I.SH.: <b>{real_name}</b>\n🎓 Guruh: <b>{student_group}</b>\n📱 Telefon: <b>{phone_number}</b>\n🌐 Til: <b>{user_lang}</b>\n📅 Ro'yxatdan o'tgan: <b>{created_at}</b>\n\n📊 <b>Imtihon Statistikasi:</b>\n• Jami topshirilgan testlar: <b>{total_attempts}</b> ta\n• O'tilgan testlar: <b>{passed_count}</b> ta\n• O'rtacha natija: <b>{avg_score}%</b>\n• Oxirgi faollik: <b>{last_active}</b>"
    },
    "admin_delete_user_confirm": {
        "en": "⚠️ <b>Are you sure you want to delete this user?</b>\n\n👤 <b>{name}</b> (ID: <code>{user_id}</code>)\n\n<i>Warning: All test attempts, scores, and statistics of this user will be permanently deleted!</i>",
        "uz": "⚠️ <b>Haqiqatan ham ushbu foydalanuvchini o'chirmoqchimisiz?</b>\n\n👤 <b>{name}</b> (ID: <code>{user_id}</code>)\n\n<i>Diqqat: Ushbu foydalanuvchining barcha topshirgan testlari va statistikasi butunlay o'chiriladi!</i>"
    },
    "admin_user_deleted": {
        "en": "🗑 User has been deleted successfully.",
        "uz": "🗑 Foydalanuvchi muvaffaqiyatli o'chirildi."
    },
    "admin_cannot_delete_admin": {
        "en": "⛔ Administrator account cannot be deleted!",
        "uz": "⛔ Administrator foydalanuvchini o'chirib bo'lmaydi!"
    },
    "btn_admin_quizzes": {
        "en": "📋 Manage Quizzes",
        "uz": "📋 Testlarni boshqarish"
    },
    "btn_admin_create_quiz": {
        "en": "➕ Create New Quiz",
        "uz": "➕ Yangi test yaratish"
    },
    "btn_admin_import": {
        "en": "📥 Bulk Import (Excel/CSV)",
        "uz": "📥 Ommaviy import (Excel/CSV)"
    },
    "btn_admin_templates": {
        "en": "📄 Download Templates",
        "uz": "📄 Shablonlarni yuklab olish"
    },
    "btn_admin_backup": {
        "en": "💾 Backup Database",
        "uz": "💾 Ma'lumotlar bazasi nusxasi"
    },
    "btn_admin_export": {
        "en": "📊 Export Results (Excel)",
        "uz": "📊 Natijalarni yuklash (Excel)"
    },
    "import_instructions": {
        "en": "📥 <b>Bulk Question Import</b>\n\nSend an <b>Excel (.xlsx)</b> or <b>CSV</b> file.\n\nRequired columns:\n• <code>question</code>\n• <code>option_a</code>\n• <code>option_b</code>\n• <code>option_c</code>\n• <code>option_d</code>\n• <code>correct_answer</code> (A, B, C, or D)\n\nOptional columns:\n• <code>explanation</code>\n• <code>topic</code>\n• <code>difficulty</code>\n• <code>timer</code>\n• <code>image</code>\n\n<i>You can upload files with 10,000+ questions!</i>",
        "uz": "📥 <b>Savollarni Ommaviy Import Qilish</b>\n\n<b>Excel (.xlsx)</b> yoki <b>CSV</b> faylni yuboring.\n\nMajburiy ustunlar:\n• <code>question</code>\n• <code>option_a</code>\n• <code>option_b</code>\n• <code>option_c</code>\n• <code>option_d</code>\n• <code>correct_answer</code> (A, B, C, yoki D)\n\nIxtiyoriy ustunlar:\n• <code>explanation</code>\n• <code>topic</code>\n• <code>difficulty</code>\n• <code>timer</code>\n• <code>image</code>\n\n<i>10,000+ gacha savolli fayllarni yuklashingiz mumkin!</i>"
    },
    "import_analyzing": {
        "en": "⏳ Analyzing and validating file rows... Please wait.",
        "uz": "⏳ Fayl tekshirilmoqda va qatorlar tekshirilmoqda... Iltimos kuting."
    },
    "import_summary": {
        "en": "📋 <b>Import Analysis Summary:</b>\n\n📁 File: <code>{filename}</code>\n🔢 Total rows scanned: <b>{total_rows}</b>\n✅ Valid questions: <b>{valid_count}</b>\n❌ Invalid rows: <b>{invalid_count}</b>\n⚠️ Duplicates detected: <b>{duplicate_count}</b>\n⏱ Parse time: <b>{duration}s</b>\n\n{error_preview}\n\nWould you like to proceed with importing these <b>{valid_count}</b> questions?",
        "uz": "📋 <b>Import Tahlili Natijasi:</b>\n\n📁 Fayl: <code>{filename}</code>\n🔢 Jami tekshirilgan qatorlar: <b>{total_rows}</b>\n✅ Yaroqli savollar: <b>{valid_count}</b>\n❌ Xato qatorlar: <b>{invalid_count}</b>\n⚠️ Takroriy savollar: <b>{duplicate_count}</b>\n⏱ Tahlil vaqti: <b>{duration} soniya</b>\n\n{error_preview}\n\nUshbu <b>{valid_count}</b> ta savolni import qilishni xohlaysizmi?"
    },
    "btn_confirm_import": {
        "en": "✅ Confirm & Import",
        "uz": "✅ Tasdiqlash va Import qilish"
    },
    "import_success": {
        "en": "🎉 <b>Successfully imported {count} questions!</b>",
        "uz": "🎉 <b>{count} ta savol muvaffaqiyatli import qilindi!</b>"
    },
    "import_cancelled": {
        "en": "❌ Import operation was cancelled.",
        "uz": "❌ Import bekor qilindi."
    },
    "quiz_created_success": {
        "en": "✅ Quiz \"<b>{title}</b>\" has been created successfully!",
        "uz": "✅ \"<b>{title}</b>\" testi muvaffaqiyatli yaratildi!"
    },
    "quiz_deleted_success": {
        "en": "🗑 Quiz has been deleted.",
        "uz": "🗑 Test o'chirildi."
    }
}

def t(key: str, lang: str = "uz", **kwargs) -> str:
    """Retrieve localized message string with fallback and variable formatting."""
    lang = lang.lower() if lang else "uz"
    if lang not in ("uz", "en"):
        lang = "uz"

    entry = TRANSLATIONS.get(key)
    if not entry:
        return key

    text = entry.get(lang) or entry.get("uz") or entry.get("en", key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text
