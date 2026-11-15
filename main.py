import asyncio
import logging
import sys
from pathlib import Path
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, BotCommandScopeDefault

import config
from bot.database.db import Database
from bot.middlewares.db_session import DatabaseMiddleware
from bot.middlewares.auth import UserMiddleware
from bot.handlers.admin import router as admin_router
from bot.handlers.group import router as group_router
from bot.handlers.student import router as student_router
from bot.handlers.common import router as common_router
from bot.services.importer import create_sample_excel_template, create_sample_csv_template

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("quizbot")

async def setup_bot_commands(bot: Bot):
    """Register menu commands visible in Telegram chat."""
    commands = [
        BotCommand(command="start", description="Start bot / Open quiz"),
        BotCommand(command="quizzes", description="Browse available quizzes"),
        BotCommand(command="myresults", description="View your past results"),
        BotCommand(command="language", description="Change interface language"),
        BotCommand(command="help", description="Show help information"),
        BotCommand(command="admin", description="Admin control panel"),
    ]
    try:
        await bot.set_my_commands(commands, scope=BotCommandScopeDefault())
    except Exception as e:
        logger.warning(f"Could not set bot commands: {e}")

async def main():
    logger.info("=" * 60)
    logger.info("STARTING TELEGRAM QUIZ BOT")
    logger.info("=" * 60)

    # Validate bot token
    if not config.BOT_TOKEN or "YOUR_TELEGRAM_BOT_TOKEN" in config.BOT_TOKEN:
        logger.error("=" * 60)
        logger.error("ERROR: BOT_TOKEN is not configured!")
        logger.error("Please edit .env file and set your Telegram Bot Token from @BotFather:")
        logger.error("BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ1234567")
        logger.error("=" * 60)
        sys.exit(1)

    # Initialize Database
    db = Database(config.DB_PATH)
    await db.init()

    # Generate sample templates if not exist
    root_sample_excel = config.BASE_DIR / "sample_questions.xlsx"
    if not root_sample_excel.exists():
        create_sample_excel_template(root_sample_excel)
        logger.info(f"Generated sample Excel: {root_sample_excel}")

    template_csv = config.TEMPLATES_DIR / "sample_questions.csv"
    if not template_csv.exists():
        create_sample_csv_template(template_csv)

    template_xlsx = config.TEMPLATES_DIR / "sample_questions.xlsx"
    if not template_xlsx.exists():
        create_sample_excel_template(template_xlsx)

    # Initialize Bot & Dispatcher
    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # Register Middlewares
    dp.update.middleware(DatabaseMiddleware(db))
    dp.update.middleware(UserMiddleware())

    # Register Handlers
    dp.include_router(admin_router)
    dp.include_router(group_router)
    dp.include_router(student_router)
    dp.include_router(common_router)

    # Configure Telegram commands
    await setup_bot_commands(bot)

    bot_user = await bot.get_me()
    logger.info(f"Bot connected: @{bot_user.username} (ID: {bot_user.id})")
    logger.info(f"Admins configured: {config.ADMIN_IDS}")
    logger.info(f"Database path: {config.DB_PATH}")
    logger.info("Polling started. Press Ctrl+C to stop.")

    try:
        await dp.start_polling(
            bot,
            allowed_updates=["message", "callback_query", "inline_query", "poll_answer", "poll"]
        )
    finally:
        await bot.session.close()
        logger.info("Bot stopped successfully.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Process terminated by user.")
