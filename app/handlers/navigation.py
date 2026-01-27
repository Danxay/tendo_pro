from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery

from ..constants import ROLE_ADMIN, ROLE_CUSTOMER, ROLE_EXECUTOR
from .common import show_admin_menu, show_customer_menu, show_executor_menu

router = Router()


@router.callback_query(F.data == "back_main")
async def back_main(callback: CallbackQuery, db) -> None:
    user = await db.get_user_by_tg_id(callback.from_user.id)
    if not user:
        await callback.answer()
        return
    await callback.answer()
    role = user.get("last_role")
    if role == ROLE_ADMIN:
        await show_admin_menu(callback.message, user, db)
    elif role == ROLE_EXECUTOR:
        await show_executor_menu(callback.message, user, db)
    else:
        await show_customer_menu(callback.message, user, db)
