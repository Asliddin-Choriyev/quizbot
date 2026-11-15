from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User as TgUser
import config
from bot.database.db import Database
from bot.database import queries

class UserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        tg_user: TgUser = data.get("event_from_user")
        if not tg_user:
            return await handler(event, data)

        db: Database = data.get("db")
        is_admin_user = config.is_admin(tg_user.id)
        data["is_admin"] = is_admin_user

        if db:
            async with db.get_connection() as conn:
                user = await queries.get_user(conn, tg_user.id)
                lang = user.language_code if user else (tg_user.language_code if tg_user.language_code in ("uz", "en") else config.DEFAULT_LANGUAGE)
                
                # Upsert user record
                user = await queries.upsert_user(
                    conn,
                    telegram_id=tg_user.id,
                    username=tg_user.username,
                    first_name=tg_user.first_name,
                    last_name=tg_user.last_name,
                    language_code=lang,
                    is_admin=is_admin_user
                )
                data["user"] = user
                data["lang"] = user.language_code
        else:
            data["lang"] = config.DEFAULT_LANGUAGE

        return await handler(event, data)
