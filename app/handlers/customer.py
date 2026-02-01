from __future__ import annotations

import html

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from ..constants import (
    MATCH_DECISION_DECLINED,
    MATCH_DECISION_LIKED,
    ORDER_STATUS_CLOSED,
    ORDER_STATUS_CLOSING_BY_CUSTOMER,
    ORDER_STATUS_OPEN,
    ROLE_CUSTOMER,
)
from ..keyboards import (
    help_keyboard,
    order_actions_keyboard,
    orders_inline,
    profile_customer_keyboard,
    responses_menu_keyboard,
)
from ..services import format_customer_profile, format_executor_card, format_order, has_match
from .common import show_customer_menu
from .registration import start_order_flow

router = Router()


def _is_customer_context(user: dict) -> bool:
    if not user or not user.get("is_customer"):
        return False
    if user.get("is_executor"):
        return user.get("last_role") == ROLE_CUSTOMER
    return True


@router.message(F.text == "Мой профиль")
async def customer_profile(message: Message, db) -> None:
    user = await db.get_user_by_tg_id(message.from_user.id)
    if not _is_customer_context(user):
        return
    text = format_customer_profile(user)
    await message.answer(text, reply_markup=profile_customer_keyboard(not user.get("is_executor")))


@router.message(F.text == "Открытые заказы")
async def customer_open_orders(message: Message, db) -> None:
    user = await db.get_user_by_tg_id(message.from_user.id)
    if not _is_customer_context(user):
        return
    orders = await db.list_orders_by_customer(user["id"])
    open_orders = [order for order in orders if order["status"] != ORDER_STATUS_CLOSED]
    if not open_orders:
        await message.answer(
            "Открытых заказов нет. Создайте новый заказ.",
            reply_markup=orders_inline(
                open_orders,
                include_new=True,
                include_back=True,
                prefix="cust_order",
                back_callback="cust_back_main",
                new_callback="cust_order_new",
            ),
        )
        return
    await message.answer(
        "Ваши открытые заказы:",
        reply_markup=orders_inline(
            open_orders,
            include_new=True,
            include_back=True,
            prefix="cust_order",
            back_callback="cust_back_main",
            new_callback="cust_order_new",
        ),
    )


@router.message(F.text == "Закрытые заказы")
async def customer_closed_orders(message: Message, db) -> None:
    user = await db.get_user_by_tg_id(message.from_user.id)
    if not _is_customer_context(user):
        return
    orders = await db.list_orders_by_customer(user["id"])
    closed_orders = [order for order in orders if order["status"] == ORDER_STATUS_CLOSED]
    if not closed_orders:
        await message.answer("Закрытых заказов нет.")
        return
    await message.answer(
        "Ваши закрытые заказы:",
        reply_markup=orders_inline(
            closed_orders,
            include_new=False,
            include_back=True,
            prefix="cust_order",
            back_callback="cust_back_main",
            new_callback="cust_order_new",
        ),
    )


@router.message(F.text == "Рейтинг")
async def customer_rating(message: Message, db) -> None:
    user = await db.get_user_by_tg_id(message.from_user.id)
    if not _is_customer_context(user):
        return
    avg, cnt = await db.get_rating_summary(user["id"])
    await message.answer(f"Ваш рейтинг: {avg:.2f} (оценок: {cnt})")


@router.message(F.text == "Помощь")
async def customer_help(message: Message, db) -> None:
    user = await db.get_user_by_tg_id(message.from_user.id)
    if not _is_customer_context(user):
        return
    await message.answer("Помощь", reply_markup=help_keyboard())


@router.callback_query(F.data == "become_executor")
async def customer_become_executor(callback: CallbackQuery, db, state) -> None:
    user = await db.get_user_by_tg_id(callback.from_user.id)
    if not user:
        await callback.answer()
        return
    data = {"phone": user.get("phone"), "tg_id": user.get("tg_id")}
    await callback.answer()
    from .registration import start_executor_registration

    await start_executor_registration(callback.message, state, db, data)


@router.callback_query(F.data == "cust_back_main")
async def customer_back_main(callback: CallbackQuery, db) -> None:
    user = await db.get_user_by_tg_id(callback.from_user.id)
    if not _is_customer_context(user):
        await callback.answer()
        return
    await callback.answer()
    await show_customer_menu(callback.message, user, db)


@router.callback_query(F.data == "cust_order_back_orders")
async def customer_back_orders(callback: CallbackQuery, db) -> None:
    user = await db.get_user_by_tg_id(callback.from_user.id)
    if not _is_customer_context(user):
        await callback.answer()
        return
    await callback.answer()
    await customer_open_orders(callback.message, db)


@router.callback_query(F.data == "cust_order_new")
async def customer_new_order(callback: CallbackQuery, db, state) -> None:
    user = await db.get_user_by_tg_id(callback.from_user.id)
    if not _is_customer_context(user):
        await callback.answer()
        return
    await callback.answer()
    await start_order_flow(callback.message, state, flow="new_order", user_id=user["id"])


@router.callback_query(F.data.startswith("cust_order:"))
async def customer_order_detail(callback: CallbackQuery, db) -> None:
    user = await db.get_user_by_tg_id(callback.from_user.id)
    if not _is_customer_context(user):
        await callback.answer()
        return
    order_id = int(callback.data.split(":", 1)[1])
    order = await db.get_order(order_id)
    if not order or order["customer_id"] != user["id"]:
        await callback.answer("Заказ не найден", show_alert=True)
        return
    if order.get("status") == ORDER_STATUS_CLOSED:
        await callback.message.edit_text(
            format_order(order),
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="Назад", callback_data="cust_back_main")]]
            ),
        )
    else:
        await callback.message.edit_text(
            format_order(order),
            reply_markup=order_actions_keyboard(order_id, for_customer=True, prefix="cust_order"),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("cust_order_edit:"))
async def customer_order_edit(callback: CallbackQuery, db, state) -> None:
    user = await db.get_user_by_tg_id(callback.from_user.id)
    if not _is_customer_context(user):
        await callback.answer()
        return
    order_id = int(callback.data.split(":", 1)[1])
    order = await db.get_order(order_id)
    if not order or order["customer_id"] != user["id"]:
        await callback.answer("Заказ не найден", show_alert=True)
        return
    await callback.answer()
    await start_order_flow(callback.message, state, flow="edit_order", user_id=user["id"], order_id=order_id)


@router.callback_query(F.data.startswith("cust_order_responses:"))
async def customer_order_responses(callback: CallbackQuery, db) -> None:
    user = await db.get_user_by_tg_id(callback.from_user.id)
    if not _is_customer_context(user):
        await callback.answer()
        return
    order_id = int(callback.data.split(":", 1)[1])
    order = await db.get_order(order_id)
    if not order or order["customer_id"] != user["id"]:
        await callback.answer("Заказ не найден", show_alert=True)
        return
    await callback.message.edit_text(
        "Отклики:",
        reply_markup=responses_menu_keyboard(order_id, prefix="cust_order"),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("cust_order_close:"))
async def customer_order_close(callback: CallbackQuery, db) -> None:
    user = await db.get_user_by_tg_id(callback.from_user.id)
    if not _is_customer_context(user):
        await callback.answer()
        return
    order_id = int(callback.data.split(":", 1)[1])
    await callback.message.edit_text(
        "Вы действительно хотите закрыть заказ?",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Да", callback_data=f"cust_close_yes:{order_id}")],
                [InlineKeyboardButton(text="Назад", callback_data=f"cust_order:{order_id}")],
            ]
        ),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("cust_close_yes:"))
async def customer_close_yes(callback: CallbackQuery, db) -> None:
    user = await db.get_user_by_tg_id(callback.from_user.id)
    if not _is_customer_context(user):
        await callback.answer()
        return
    order_id = int(callback.data.split(":", 1)[1])
    order = await db.get_order(order_id)
    if not order or order["customer_id"] != user["id"]:
        await callback.answer("Заказ не найден", show_alert=True)
        return
    if order.get("assigned_executor_id"):
        await db.set_order_status(order_id, ORDER_STATUS_CLOSING_BY_CUSTOMER)
        executor = await db.get_user_by_id(order.get("assigned_executor_id"))
        if executor and executor.get("tg_id"):
            await callback.bot.send_message(
                executor["tg_id"],
                f"Добрый день! Заказчик закрыл заказ {order_id} {html.escape(order.get('name','') or '')}. Подтвердите закрытие.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="Подтвердить закрытие", callback_data=f"exec_close_confirm:{order_id}")]
                    ]
                ),
            )
        await callback.message.edit_text("Ожидайте подтверждение исполнителя")
    else:
        await db.set_order_status(order_id, ORDER_STATUS_CLOSED)
        await callback.message.edit_text("Заказ закрыт.")
    await callback.answer()


async def _next_executor_candidate(order_id: int, db) -> dict | None:
    order = await db.get_order(order_id)
    if not order:
        return None
    if order.get("assigned_executor_id"):
        return None
    matches = await db.list_matches_for_order(order_id)
    seen = {m["executor_id"] for m in matches if m.get("customer_decision")}
    declined_by_executor = {m["executor_id"] for m in matches if m.get("executor_decision") == MATCH_DECISION_DECLINED}
    executors = await db.list_executor_profiles()
    for executor in executors:
        if executor.get("blocked"):
            continue
        if executor["user_id"] in seen or executor["user_id"] in declined_by_executor:
            continue
        if not has_match(order, executor):
            continue
        return executor
    return None


@router.callback_query(F.data.startswith("cust_order_responses_new:"))
async def customer_responses_new(callback: CallbackQuery, db) -> None:
    order_id = int(callback.data.split(":", 1)[1])
    user = await db.get_user_by_tg_id(callback.from_user.id)
    order = await db.get_order(order_id)
    if not user or not order or order.get("customer_id") != user.get("id"):
        await callback.answer("Заказ не найден", show_alert=True)
        return
    executor = await _next_executor_candidate(order_id, db)
    if not executor:
        await callback.message.edit_text(
            "Доступные исполнители закончились",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="Назад", callback_data=f"cust_order_responses:{order_id}")]]
            ),
        )
        await callback.answer()
        return
    text = format_executor_card(executor)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Да", callback_data=f"cust_candidate_yes:{order_id}:{executor['user_id']}"
                ),
                InlineKeyboardButton(
                    text="Нет", callback_data=f"cust_candidate_no:{order_id}:{executor['user_id']}"
                ),
            ],
            [InlineKeyboardButton(text="Назад", callback_data=f"cust_order_responses:{order_id}")],
        ]
    )
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("cust_candidate_yes:"))
async def customer_candidate_yes(callback: CallbackQuery, db) -> None:
    _, order_id, executor_id = callback.data.split(":")
    order_id = int(order_id)
    executor_id = int(executor_id)
    user = await db.get_user_by_tg_id(callback.from_user.id)
    order = await db.get_order(order_id)
    if not user or not order or order.get("customer_id") != user.get("id"):
        await callback.answer("Недостаточно прав", show_alert=True)
        return
    await db.upsert_match(order_id, executor_id, customer_decision=MATCH_DECISION_LIKED)
    executor = await db.get_user_by_id(executor_id)
    if executor and executor.get("tg_id"):
        await callback.bot.send_message(
            executor["tg_id"],
            "Добрый день! Вас выбрали исполнителем. Ознакомитесь в разделе Возможные заказы в пункте Вас выбрали",
        )
    await callback.answer("Добавлено в принятые")
    await customer_responses_new(callback, db)


@router.callback_query(F.data.startswith("cust_candidate_no:"))
async def customer_candidate_no(callback: CallbackQuery, db) -> None:
    _, order_id, executor_id = callback.data.split(":")
    order_id = int(order_id)
    executor_id = int(executor_id)
    user = await db.get_user_by_tg_id(callback.from_user.id)
    order = await db.get_order(order_id)
    if not user or not order or order.get("customer_id") != user.get("id"):
        await callback.answer("Недостаточно прав", show_alert=True)
        return
    await db.upsert_match(order_id, executor_id, customer_decision=MATCH_DECISION_DECLINED)
    await callback.answer("Добавлено в отказанные")
    await customer_responses_new(callback, db)


@router.callback_query(F.data.startswith("cust_order_responses_liked:"))
async def customer_responses_liked(callback: CallbackQuery, db) -> None:
    order_id = int(callback.data.split(":", 1)[1])
    user = await db.get_user_by_tg_id(callback.from_user.id)
    order = await db.get_order(order_id)
    if not user or not order or order.get("customer_id") != user.get("id"):
        await callback.answer("Заказ не найден", show_alert=True)
        return
    matches = await db.list_customer_likes(order_id)
    if not matches:
        await callback.message.edit_text(
            "Принятых исполнителей нет.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="Назад", callback_data=f"cust_order_responses:{order_id}")]]
            ),
        )
        await callback.answer()
        return
    lines = []
    buttons = []
    for match in matches:
        executor = await db.get_user_by_id(match["executor_id"])
        status = "принял" if match.get("executor_decision") == MATCH_DECISION_LIKED else "ожидает"
        phone_line = f"Телефон: {executor.get('phone','-')}" if match.get("executor_decision") == MATCH_DECISION_LIKED else ""

        first_name_raw = executor.get("first_name", "") or ""
        first_name = html.escape(first_name_raw)
        last_name = html.escape(executor.get("last_name", "") or "")

        lines.append(
            f"{first_name} {last_name} - {status} {phone_line}".strip()
        )
        if match.get("executor_decision") == MATCH_DECISION_LIKED:
            buttons.append(
                [
                    InlineKeyboardButton(
                        text=f"Подтвердить: {first_name_raw}",
                        callback_data=f"cust_confirm_exec:{order_id}:{executor['id']}",
                    )
                ]
            )
    buttons.append([InlineKeyboardButton(text="Назад", callback_data=f"cust_order_responses:{order_id}")])
    lines.append(
        "Подтвердите исполнителя. Ваш заказ будет показываться до тех пор, пока Вы не подтвердите исполнителя."
    )
    await callback.message.edit_text("\n".join(lines), reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()


@router.callback_query(F.data.startswith("cust_confirm_exec:"))
async def customer_confirm_executor(callback: CallbackQuery, db) -> None:
    _, order_id, executor_id = callback.data.split(":")
    order_id = int(order_id)
    executor_id = int(executor_id)
    user = await db.get_user_by_tg_id(callback.from_user.id)
    order = await db.get_order(order_id)
    if not user or not order or order.get("customer_id") != user.get("id"):
        await callback.answer("Недостаточно прав", show_alert=True)
        return
    await db.assign_executor(order_id, executor_id)
    await callback.answer("Исполнитель подтвержден")
    executor = await db.get_user_by_id(executor_id)
    if executor and executor.get("tg_id"):
        await callback.bot.send_message(
            executor["tg_id"],
            f"Заказчик подтвердил исполнителя по заказу {order_id} {html.escape(order.get('name','') or '')}.",
        )
    await callback.message.edit_text("Исполнитель подтвержден. Заказ закреплен.")


@router.callback_query(F.data.startswith("cust_order_responses_declined:"))
async def customer_responses_declined(callback: CallbackQuery, db) -> None:
    order_id = int(callback.data.split(":", 1)[1])
    user = await db.get_user_by_tg_id(callback.from_user.id)
    order = await db.get_order(order_id)
    if not user or not order or order.get("customer_id") != user.get("id"):
        await callback.answer("Заказ не найден", show_alert=True)
        return
    matches = await db.list_customer_declines(order_id)
    if not matches:
        await callback.message.edit_text(
            "Отказанных исполнителей нет.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="Назад", callback_data=f"cust_order_responses:{order_id}")]]
            ),
        )
        await callback.answer()
        return
    buttons = []
    lines = []
    for match in matches:
        executor = await db.get_user_by_id(match["executor_id"])
        first_name_raw = executor.get("first_name", "") or ""
        first_name = html.escape(first_name_raw)
        last_name = html.escape(executor.get("last_name", "") or "")
        lines.append(f"{first_name} {last_name}")
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"Изменить решение: {first_name_raw}",
                    callback_data=f"cust_change_decision:{order_id}:{executor['id']}",
                )
            ]
        )
    buttons.append([InlineKeyboardButton(text="Назад", callback_data=f"cust_order_responses:{order_id}")])
    await callback.message.edit_text("\n".join(lines), reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()


@router.callback_query(F.data.startswith("cust_change_decision:"))
async def customer_change_decision(callback: CallbackQuery, db) -> None:
    _, order_id, executor_id = callback.data.split(":")
    order_id = int(order_id)
    executor_id = int(executor_id)
    user = await db.get_user_by_tg_id(callback.from_user.id)
    order = await db.get_order(order_id)
    if not user or not order or order.get("customer_id") != user.get("id"):
        await callback.answer("Недостаточно прав", show_alert=True)
        return
    await db.update_match_decision(order_id, executor_id, customer_decision=MATCH_DECISION_LIKED)
    await callback.answer("Исполнитель добавлен в принятые")
    executor = await db.get_user_by_id(executor_id)
    if executor and executor.get("tg_id"):
        await callback.bot.send_message(
            executor["tg_id"],
            "Добрый день! Вас выбрали исполнителем. Ознакомитесь в разделе Возможные заказы в пункте Вас выбрали",
        )
    await callback.message.edit_text("Решение изменено.")
