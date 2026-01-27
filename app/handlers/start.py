from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from ..constants import ROLE_ADMIN, ROLE_CUSTOMER, ROLE_EXECUTOR
from ..keyboards import contact_keyboard, role_keyboard, start_keyboard
from ..states import AuthStates
from ..validation import normalize_phone
from .common import show_admin_menu, show_customer_menu, show_executor_menu, show_role_choice
from .registration import start_customer_registration, start_executor_registration

router = Router()

INTRO_TEXT = (
    "Что может этот бот: Данный бот предназначен для размещения заказов по проектированию "
    "различных разделов проектной документации, рабочей документации и исполнительной "
    "документации, а также поиска исполнителей на различные разделы"
)


@router.message(CommandStart())
async def command_start(message: Message, state: FSMContext, db, config) -> None:
    await state.clear()
    user = await db.get_user_by_tg_id(message.from_user.id)
    if user:
        if user.get("blocked"):
            await message.answer("Вы заблокированы администрацией.")
            return
        await db.update_user_tg(user["id"], message.from_user.id)
        if user.get("is_admin"):
            await show_admin_menu(message, user, db)
            return
        if user.get("is_customer") and user.get("is_executor"):
            await show_role_choice(message)
            return
        if user.get("is_customer"):
            await show_customer_menu(message, user, db)
            return
        if user.get("is_executor"):
            await show_executor_menu(message, user, db)
            return
    await message.answer(INTRO_TEXT, reply_markup=start_keyboard())


@router.message(F.text == "Запустить")
async def start_pressed(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "Просим предоставить контактный номер телефона",
        reply_markup=contact_keyboard("Ввести номер"),
    )


@router.message(F.contact)
async def contact_received(message: Message, state: FSMContext, db, config) -> None:
    contact = message.contact
    if contact.user_id and contact.user_id != message.from_user.id:
        await message.answer("Пожалуйста, отправьте свой собственный номер телефона.")
        return
    phone = normalize_phone(contact.phone_number)
    if not phone:
        await message.answer("Не удалось распознать номер. Попробуйте еще раз.")
        return

    await state.update_data(phone=phone, tg_id=message.from_user.id)

    if await db.is_admin_phone(phone):
        await state.set_state(AuthStates.waiting_admin_code)
        await message.answer("Введите код администратора")
        return

    user = await db.get_user_by_phone(phone)
    if user:
        await db.update_user_tg(user["id"], message.from_user.id)
        if user.get("is_customer") and user.get("is_executor"):
            await show_role_choice(message)
            return
        if user.get("is_customer"):
            await show_customer_menu(message, user, db)
            return
        if user.get("is_executor"):
            await show_executor_menu(message, user, db)
            return
        await show_role_choice(message)
        return

    await state.set_state(AuthStates.choosing_role)
    await message.answer("Выберите роль", reply_markup=role_keyboard())


@router.message(AuthStates.waiting_admin_code)
async def admin_code_entered(message: Message, state: FSMContext, db, config) -> None:
    code = (message.text or "").strip()
    data = await state.get_data()
    phone = data.get("phone")
    tg_id = data.get("tg_id")
    if code != config.admin_code:
        await message.answer("Неверный код. Попробуйте еще раз.")
        return
    user = await db.get_user_by_phone(phone)
    if not user:
        user = await db.create_user(tg_id, phone)
    await db.set_user_roles(user["id"], is_admin=True)
    await db.update_user_tg(user["id"], tg_id)
    await state.clear()
    user = await db.get_user_by_phone(phone)
    await show_admin_menu(message, user, db)


@router.message(AuthStates.choosing_role, F.text == "Заказчик")
async def choose_customer(message: Message, state: FSMContext, db) -> None:
    data = await state.get_data()
    await state.clear()
    await start_customer_registration(message, state, db, data)


@router.message(AuthStates.choosing_role, F.text == "Исполнитель")
async def choose_executor(message: Message, state: FSMContext, db) -> None:
    data = await state.get_data()
    await state.clear()
    await start_executor_registration(message, state, db, data)


@router.message(F.text == "Заказчик")
async def switch_to_customer(message: Message, state: FSMContext, db) -> None:
    if await state.get_state():
        return
    user = await db.get_user_by_tg_id(message.from_user.id)
    if user and user.get("is_customer"):
        await show_customer_menu(message, user, db)


@router.message(F.text == "Исполнитель")
async def switch_to_executor(message: Message, state: FSMContext, db) -> None:
    if await state.get_state():
        return
    user = await db.get_user_by_tg_id(message.from_user.id)
    if user and user.get("is_executor"):
        await show_executor_menu(message, user, db)
