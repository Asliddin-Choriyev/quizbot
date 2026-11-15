from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from bot.utils.i18n import t

def get_cancel_reply_kb(lang: str = "uz") -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t("btn_cancel", lang))]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def get_skip_cancel_kb(lang: str = "uz") -> ReplyKeyboardMarkup:
    skip_btn = "⏭ O'tkazib yuborish" if lang == "uz" else "⏭ Skip"
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=skip_btn)],
            [KeyboardButton(text=t("btn_cancel", lang))]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def get_phone_request_kb(lang: str = "uz") -> ReplyKeyboardMarkup:
    phone_btn = "📱 Telefon raqamni yuborish" if lang == "uz" else "📱 Send Phone Number"
    skip_btn = "⏭ O'tkazib yuborish" if lang == "uz" else "⏭ Skip"
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=phone_btn, request_contact=True)],
            [KeyboardButton(text=skip_btn)],
            [KeyboardButton(text=t("btn_cancel", lang))]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
