from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

from ..constants import (
    CONSTRUCTION_TYPES,
    DOC_TYPES,
    EXPERIENCE_OPTIONS,
    ORDER_STATUS_OPEN,
    ROLE_CUSTOMER,
    ROLE_EXECUTOR,
    SECTIONS_CAPITAL,
    SECTIONS_LINEAR,
    YES_NO,
)
from ..keyboards import multiselect_keyboard
from ..states import CustomerReg, ExecutorReg, OrderFlow
from ..validation import count_words, is_valid_name, is_valid_url, parse_date
from .common import show_customer_menu, show_executor_menu

router = Router()

SKIP_KB = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Пропустить")]],
    resize_keyboard=True,
    one_time_keyboard=True,
)

EXPERIENCE_KB = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text=opt)] for opt in EXPERIENCE_OPTIONS],
    resize_keyboard=True,
    one_time_keyboard=True,
)

YES_NO_KB = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text=opt)] for opt in YES_NO],
    resize_keyboard=True,
    one_time_keyboard=True,
)


def _selected_values(options: list[str], selected_indices: list[int]) -> list[str]:
    return [options[i] for i in selected_indices if 0 <= i < len(options)]


def _is_state(current: str | None, state) -> bool:
    return current == state.state


async def start_customer_registration(message: Message, state: FSMContext, db, data: dict) -> None:
    await state.clear()
    await state.update_data(flow="customer_registration", phone=data.get("phone"), tg_id=data.get("tg_id"))
    await state.set_state(CustomerReg.first_name)
    await message.answer("Введите ваше Имя", reply_markup=ReplyKeyboardRemove())


async def start_executor_registration(message: Message, state: FSMContext, db, data: dict) -> None:
    await state.clear()
    await state.update_data(flow="executor_registration", phone=data.get("phone"), tg_id=data.get("tg_id"))
    await state.set_state(ExecutorReg.first_name)
    await message.answer("Введите ваше Имя", reply_markup=ReplyKeyboardRemove())


async def start_order_flow(message: Message, state: FSMContext, flow: str, user_id: int, order_id: int | None = None) -> None:
    await state.clear()
    await state.update_data(flow=flow, user_id=user_id, edit_order_id=order_id)
    await state.set_state(OrderFlow.order_name)
    await message.answer("Введите наименование заказа", reply_markup=ReplyKeyboardRemove())


async def start_executor_edit(message: Message, state: FSMContext, user_id: int) -> None:
    await state.clear()
    await state.update_data(flow="executor_edit", user_id=user_id)
    await state.set_state(ExecutorReg.org_name)
    await message.answer("Введите наименование организации или нажмите Пропустить", reply_markup=SKIP_KB)


@router.message(CustomerReg.first_name)
async def customer_first_name(message: Message, state: FSMContext) -> None:
    if not is_valid_name(message.text):
        await message.answer("Не похоже на имя. Попробуйте еще раз")
        return
    await state.update_data(first_name=message.text.strip())
    await state.set_state(CustomerReg.last_name)
    await message.answer("Введите вашу Фамилию")


@router.message(CustomerReg.last_name)
async def customer_last_name(message: Message, state: FSMContext) -> None:
    if not is_valid_name(message.text):
        await message.answer("Не похоже на фамилию. Попробуйте еще раз")
        return
    await state.update_data(last_name=message.text.strip())
    await state.set_state(CustomerReg.org_name)
    await message.answer("Введите наименование организации или нажмите Пропустить", reply_markup=SKIP_KB)


@router.message(CustomerReg.org_name)
async def customer_org(message: Message, state: FSMContext) -> None:
    org_name = None if message.text == "Пропустить" else (message.text or "").strip()
    await state.update_data(org_name=org_name)
    await state.set_state(OrderFlow.order_name)
    await message.answer("Введите наименование заказа", reply_markup=ReplyKeyboardRemove())


@router.message(OrderFlow.order_name)
async def order_name(message: Message, state: FSMContext) -> None:
    if not message.text or not message.text.strip():
        await message.answer("Наименование заказа обязательно")
        return
    await state.update_data(order_name=message.text.strip())
    await state.set_state(OrderFlow.doc_types)
    await state.update_data(multiselect_options=DOC_TYPES, multiselect_selected=[])
    await message.answer("Укажите вид документации (можно выбрать несколько)", reply_markup=multiselect_keyboard(DOC_TYPES, set()))


@router.message(ExecutorReg.first_name)
async def executor_first_name(message: Message, state: FSMContext) -> None:
    if not is_valid_name(message.text):
        await message.answer("Не похоже на имя. Попробуйте еще раз")
        return
    await state.update_data(first_name=message.text.strip())
    await state.set_state(ExecutorReg.last_name)
    await message.answer("Введите вашу Фамилию")


@router.message(ExecutorReg.last_name)
async def executor_last_name(message: Message, state: FSMContext) -> None:
    if not is_valid_name(message.text):
        await message.answer("Не похоже на фамилию. Попробуйте еще раз")
        return
    await state.update_data(last_name=message.text.strip())
    await state.set_state(ExecutorReg.org_name)
    await message.answer("Введите наименование организации или нажмите Пропустить", reply_markup=SKIP_KB)


@router.message(ExecutorReg.org_name)
async def executor_org(message: Message, state: FSMContext) -> None:
    org_name = None if message.text == "Пропустить" else (message.text or "").strip()
    await state.update_data(org_name=org_name)
    await state.set_state(ExecutorReg.experience)
    await message.answer("Опыт работы", reply_markup=EXPERIENCE_KB)


@router.message(ExecutorReg.experience)
async def executor_experience(message: Message, state: FSMContext) -> None:
    if message.text not in EXPERIENCE_OPTIONS:
        await message.answer("Выберите вариант из списка")
        return
    await state.update_data(experience=message.text)
    await state.set_state(ExecutorReg.resume)
    await message.answer(
        "Прикрепите резюме (ссылка) или опишите выполненные заказы (до 100 слов)",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(ExecutorReg.resume)
async def executor_resume(message: Message, state: FSMContext) -> None:
    import re

    text = (message.text or "").strip()
    resume_link = None
    resume_text = None
    urls = re.findall(r"https?://\\S+", text)
    if urls:
        resume_link = urls[0]
        cleaned = text.replace(resume_link, "").strip()
        if cleaned:
            if count_words(cleaned) > 100:
                await message.answer("Слишком длинный текст. Укажите до 100 слов.")
                return
            resume_text = cleaned
    else:
        if count_words(text) > 100:
            await message.answer("Слишком длинный текст. Укажите до 100 слов.")
            return
        resume_text = text
    await state.update_data(resume_link=resume_link, resume_text=resume_text)
    await state.set_state(ExecutorReg.doc_types)
    await state.update_data(multiselect_options=DOC_TYPES, multiselect_selected=[])
    await message.answer("Укажите вид разрабатываемой документации (можно выбрать несколько)", reply_markup=multiselect_keyboard(DOC_TYPES, set()))


@router.callback_query(F.data.startswith("multi:"))
async def multiselect_toggle(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    options = data.get("multiselect_options", [])
    selected = set(data.get("multiselect_selected", []))
    try:
        idx = int(callback.data.split(":", 1)[1])
    except ValueError:
        await callback.answer()
        return
    if idx in selected:
        selected.remove(idx)
    else:
        selected.add(idx)
    await state.update_data(multiselect_selected=list(selected))
    await callback.message.edit_reply_markup(reply_markup=multiselect_keyboard(options, selected))
    await callback.answer()


async def _ask_next_order_sections(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    pending = data.get("pending_sections", [])
    if not pending:
        await state.set_state(OrderFlow.description)
        await message.answer("Укажите кратко что необходимо сделать (до 50 слов)")
        return
    next_type = pending.pop(0)
    await state.update_data(pending_sections=pending)
    if next_type == "capital":
        await state.set_state(OrderFlow.sections_capital)
        await state.update_data(multiselect_options=SECTIONS_CAPITAL, multiselect_selected=[])
        await message.answer(
            "Укажите требуемые разделы (кап. строительство)",
            reply_markup=multiselect_keyboard(SECTIONS_CAPITAL, set()),
        )
    else:
        await state.set_state(OrderFlow.sections_linear)
        await state.update_data(multiselect_options=SECTIONS_LINEAR, multiselect_selected=[])
        await message.answer(
            "Укажите требуемые разделы (линейные объекты)",
            reply_markup=multiselect_keyboard(SECTIONS_LINEAR, set()),
        )


async def _ask_next_executor_sections(message: Message, state: FSMContext, db) -> None:
    data = await state.get_data()
    pending = data.get("pending_sections", [])
    if not pending:
        await _finish_executor_registration(message, state, db)
        return
    next_type = pending.pop(0)
    await state.update_data(pending_sections=pending)
    if next_type == "capital":
        await state.set_state(ExecutorReg.sections_capital)
        await state.update_data(multiselect_options=SECTIONS_CAPITAL, multiselect_selected=[])
        await message.answer(
            "Укажите разделы (кап. строительство)",
            reply_markup=multiselect_keyboard(SECTIONS_CAPITAL, set()),
        )
    else:
        await state.set_state(ExecutorReg.sections_linear)
        await state.update_data(multiselect_options=SECTIONS_LINEAR, multiselect_selected=[])
        await message.answer(
            "Укажите разделы (линейные объекты)",
            reply_markup=multiselect_keyboard(SECTIONS_LINEAR, set()),
        )


@router.callback_query(F.data == "multi_done")
async def multiselect_done(callback: CallbackQuery, state: FSMContext, db) -> None:
    data = await state.get_data()
    options = data.get("multiselect_options", [])
    selected = data.get("multiselect_selected", [])
    if not selected:
        await callback.answer("Выберите хотя бы один вариант", show_alert=True)
        return
    selected_values = _selected_values(options, selected)
    current_state = await state.get_state()

    if _is_state(current_state, OrderFlow.doc_types):
        await state.update_data(doc_types=selected_values)
        await state.set_state(OrderFlow.construction_types)
        await state.update_data(multiselect_options=CONSTRUCTION_TYPES, multiselect_selected=[])
        await callback.message.answer(
            "Укажите вид строительства (можно выбрать несколько)",
            reply_markup=multiselect_keyboard(CONSTRUCTION_TYPES, set()),
        )
        await callback.answer()
        return

    if _is_state(current_state, OrderFlow.construction_types):
        await state.update_data(construction_types=selected_values)
        pending = []
        if CONSTRUCTION_TYPES[0] in selected_values:
            pending.append("capital")
        if CONSTRUCTION_TYPES[1] in selected_values:
            pending.append("linear")
        await state.update_data(pending_sections=pending)
        await callback.answer()
        await _ask_next_order_sections(callback.message, state)
        return

    if _is_state(current_state, OrderFlow.sections_capital):
        await state.update_data(sections_capital=selected_values)
        await callback.answer()
        await _ask_next_order_sections(callback.message, state)
        return

    if _is_state(current_state, OrderFlow.sections_linear):
        await state.update_data(sections_linear=selected_values)
        await callback.answer()
        await _ask_next_order_sections(callback.message, state)
        return

    if _is_state(current_state, ExecutorReg.doc_types):
        await state.update_data(doc_types=selected_values)
        await state.set_state(ExecutorReg.construction_types)
        await state.update_data(multiselect_options=CONSTRUCTION_TYPES, multiselect_selected=[])
        await callback.message.answer(
            "Укажите вид строительства (можно выбрать несколько)",
            reply_markup=multiselect_keyboard(CONSTRUCTION_TYPES, set()),
        )
        await callback.answer()
        return

    if _is_state(current_state, ExecutorReg.construction_types):
        await state.update_data(construction_types=selected_values)
        pending = []
        if CONSTRUCTION_TYPES[0] in selected_values:
            pending.append("capital")
        if CONSTRUCTION_TYPES[1] in selected_values:
            pending.append("linear")
        await state.update_data(pending_sections=pending)
        await callback.answer()
        await _ask_next_executor_sections(callback.message, state, db)
        return

    if _is_state(current_state, ExecutorReg.sections_capital):
        await state.update_data(sections_capital=selected_values)
        await callback.answer()
        await _ask_next_executor_sections(callback.message, state, db)
        return

    if _is_state(current_state, ExecutorReg.sections_linear):
        await state.update_data(sections_linear=selected_values)
        await callback.answer()
        await _ask_next_executor_sections(callback.message, state, db)
        return

    await callback.answer()


@router.message(OrderFlow.description)
async def order_description(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if count_words(text) > 50:
        await message.answer("Слишком длинное описание. Укажите до 50 слов.")
        return
    await state.update_data(description=text)
    await state.set_state(OrderFlow.deadline)
    await message.answer("Укажите срок исполнения (ДД.ММ.ГГГГ или ГГГГ-ММ-ДД)")


@router.message(OrderFlow.deadline)
async def order_deadline(message: Message, state: FSMContext) -> None:
    date_val = parse_date(message.text or "")
    if not date_val:
        await message.answer("Не похоже на дату. Укажите в формате ДД.ММ.ГГГГ")
        return
    await state.update_data(deadline=date_val.isoformat())
    await state.set_state(OrderFlow.price)
    await message.answer("Укажите ориентировочную цену")


@router.message(OrderFlow.price)
async def order_price(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if not text:
        await message.answer("Цена обязательна")
        return
    await state.update_data(price=text)
    await state.set_state(OrderFlow.expertise_required)
    await message.answer("Укажите необходимость проходить ГГЭ или другую экспертизу", reply_markup=YES_NO_KB)


@router.message(OrderFlow.expertise_required)
async def order_expertise(message: Message, state: FSMContext) -> None:
    if message.text not in YES_NO:
        await message.answer("Выберите вариант из списка")
        return
    await state.update_data(expertise_required=message.text == "Да")
    await state.set_state(OrderFlow.files_link)
    await message.answer("Приложите ссылку на облачное хранение", reply_markup=ReplyKeyboardRemove())


@router.message(OrderFlow.files_link)
async def order_files(message: Message, state: FSMContext, db) -> None:
    link = (message.text or "").strip()
    if not is_valid_url(link):
        await message.answer("Не похоже на ссылку. Вставьте ссылку на облачное хранение")
        return
    await state.update_data(files_link=link)

    data = await state.get_data()
    flow = data.get("flow")
    user_id = data.get("user_id")
    if flow == "customer_registration":
        phone = data.get("phone")
        tg_id = data.get("tg_id")
        user = await db.get_user_by_phone(phone)
        if not user:
            user = await db.create_user(tg_id, phone)
        await db.update_user_profile(user["id"], data.get("first_name"), data.get("last_name"), data.get("org_name"))
        await db.set_user_roles(user["id"], is_customer=True)
        user_id = user["id"]
    elif flow == "new_order":
        user = await db.get_user_by_id(user_id)
        if not user:
            await state.clear()
            await message.answer("Пользователь не найден. Начните сначала.")
            return
    elif flow == "edit_order":
        pass

    order_payload = {
        "name": data.get("order_name"),
        "doc_types": data.get("doc_types", []),
        "construction_types": data.get("construction_types", []),
        "sections_capital": data.get("sections_capital", []),
        "sections_linear": data.get("sections_linear", []),
        "description": data.get("description"),
        "deadline": data.get("deadline"),
        "price": data.get("price"),
        "expertise_required": data.get("expertise_required"),
        "files_link": data.get("files_link"),
        "status": ORDER_STATUS_OPEN,
    }

    if flow == "edit_order":
        order_id = data.get("edit_order_id")
        await state.update_data(pending_order_payload=order_payload, edit_order_id=order_id)
        await state.set_state(OrderFlow.confirm_save)
        await message.answer(
            "Сохранить изменения?",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="Сохранить", callback_data=f"order_save:{order_id}")],
                    [InlineKeyboardButton(text="Назад", callback_data=f"order_discard:{order_id}")],
                ]
            ),
        )
        return

    await db.create_order(user_id, order_payload)
    await message.answer("Заказ создан.")
    await state.clear()
    user = await db.get_user_by_id(user_id)
    await show_customer_menu(message, user, db)


@router.callback_query(F.data.startswith("order_save:"))
async def order_save(callback: CallbackQuery, state: FSMContext, db) -> None:
    data = await state.get_data()
    order_id = data.get("edit_order_id")
    payload = data.get("pending_order_payload")
    if not order_id or not payload:
        await callback.answer("Нет данных для сохранения", show_alert=True)
        return
    await db.update_order(order_id, payload)
    await state.clear()
    user = await db.get_user_by_tg_id(callback.from_user.id)
    await callback.message.answer("Заказ обновлен.")
    if user:
        await show_customer_menu(callback.message, user, db)
    await callback.answer()


@router.callback_query(F.data.startswith("order_discard:"))
async def order_discard(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.answer(
        "Изменения не сохранены. Сохранить изменения?",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Да", callback_data=callback.data.replace("order_discard", "order_save"))],
                [InlineKeyboardButton(text="Нет", callback_data="order_discard_no")],
            ]
        ),
    )
    await callback.answer()


@router.callback_query(F.data == "order_discard_no")
async def order_discard_no(callback: CallbackQuery, state: FSMContext, db) -> None:
    await state.clear()
    user = await db.get_user_by_tg_id(callback.from_user.id)
    if user:
        await show_customer_menu(callback.message, user, db)
    await callback.answer()


async def _finish_executor_registration(message: Message, state: FSMContext, db) -> None:
    data = await state.get_data()
    flow = data.get("flow")
    phone = data.get("phone")
    tg_id = data.get("tg_id")
    user = None
    if flow in {"executor_registration", "executor_edit"}:
        if phone:
            user = await db.get_user_by_phone(phone)
        if not user and data.get("user_id"):
            user = await db.get_user_by_id(data.get("user_id"))
        if not user:
            user = await db.create_user(tg_id, phone)
        await db.update_user_profile(
            user["id"],
            data.get("first_name") or user.get("first_name") or "-",
            data.get("last_name") or user.get("last_name") or "-",
            data.get("org_name"),
        )
        await db.set_user_roles(user["id"], is_executor=True)
        await db.upsert_executor_profile(
            user["id"],
            data.get("experience"),
            data.get("resume_link"),
            data.get("resume_text"),
            data.get("doc_types", []),
            data.get("construction_types", []),
            data.get("sections_capital", []),
            data.get("sections_linear", []),
        )
        await state.clear()
        await message.answer("Профиль исполнителя сохранен.")
        await show_executor_menu(message, user, db)
