from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

from ..states import HelpState

router = Router()


@router.callback_query(F.data == "help_new")
async def help_new(callback: CallbackQuery, state: FSMContext, db) -> None:
    user = await db.get_user_by_tg_id(callback.from_user.id)
    if not user:
        await callback.answer()
        return
    await state.set_state(HelpState.waiting_text)
    await state.update_data(role=user.get("last_role", ""), user_id=user.get("id"))
    await callback.message.edit_text("Опишите проблему одним сообщением")
    await callback.answer()


@router.message(HelpState.waiting_text)
async def help_text(message: Message, state: FSMContext, db) -> None:
    text = (message.text or "").strip()
    if not text:
        await message.answer("Сообщение не может быть пустым")
        return
    data = await state.get_data()
    await db.add_help_message(data.get("user_id"), data.get("role") or "", text)
    admins = [u for u in await db.list_users() if u.get("is_admin")]
    for admin in admins:
        if admin.get("tg_id"):
            await message.bot.send_message(
                admin["tg_id"],
                f"Новое сообщение в помощь от {message.from_user.full_name} ({data.get('role')}):\n{text}",
            )
    await message.answer("Сообщение отправлено администрации.")
    await state.clear()
