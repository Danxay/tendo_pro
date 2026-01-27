from __future__ import annotations

from aiogram.types import Message

from ..constants import ROLE_ADMIN, ROLE_CUSTOMER, ROLE_EXECUTOR
from ..keyboards import admin_main_keyboard, customer_main_keyboard, executor_main_keyboard, role_keyboard


async def show_customer_menu(message: Message, user: dict, db) -> None:
    await db.set_last_role(user["id"], ROLE_CUSTOMER)
    await message.answer("Главное меню (Заказчик)", reply_markup=customer_main_keyboard())


async def show_executor_menu(message: Message, user: dict, db) -> None:
    await db.set_last_role(user["id"], ROLE_EXECUTOR)
    await message.answer("Главное меню (Исполнитель)", reply_markup=executor_main_keyboard())


async def show_admin_menu(message: Message, user: dict, db) -> None:
    await db.set_last_role(user["id"], ROLE_ADMIN)
    await message.answer("Меню администратора", reply_markup=admin_main_keyboard())


async def show_role_choice(message: Message) -> None:
    await message.answer("Выберите роль", reply_markup=role_keyboard())
