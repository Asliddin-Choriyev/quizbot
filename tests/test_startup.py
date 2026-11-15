import pytest
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from bot.database.db import Database
from bot.middlewares.db_session import DatabaseMiddleware
from bot.middlewares.auth import UserMiddleware
from bot.handlers import admin_router, group_router, student_router, common_router

def test_router_assembly():
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(admin_router)
    dp.include_router(group_router)
    dp.include_router(student_router)
    dp.include_router(common_router)

    # Check that routers are properly registered
    sub_routers = dp.sub_routers
    assert len(sub_routers) == 4
    names = [r.name for r in sub_routers]
    assert "admin" in names
    assert "group" in names
    assert "student" in names
    assert "common" in names

@pytest.mark.asyncio
async def test_bot_startup_check(tmp_path):
    # Verify DB initialization runs cleanly on startup
    db = Database(tmp_path / "startup.db")
    await db.init()
    assert (tmp_path / "startup.db").exists()
