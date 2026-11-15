from bot.handlers.common import router as common_router
from bot.handlers.student import router as student_router
from bot.handlers.group import router as group_router
from bot.handlers.admin import router as admin_router

__all__ = ["common_router", "student_router", "group_router", "admin_router"]
