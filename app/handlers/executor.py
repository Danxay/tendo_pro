from __future__ import annotations

import html

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from ..constants import (
    MATCH_DECISION_DECLINED,
    MATCH_DECISION_LIKED,
    ORDER_STATUS_CLOSED,
    ORDER_STATUS_CLOSING_BY_EXECUTOR,
    ROLE_EXECUTOR,
)
from ..keyboards import (
    help_keyboard,
    order_actions_keyboard,
    orders_inline,
    possible_orders_keyboard,
    profile_executor_keyboard,
    rating_keyboard,
)
from ..services import format_executor_profile, format_order, has_match
from .common import show_executor_menu
from .registration import start_customer_registration, start_executor_edit

router = Router()


def _is_executor_context(user: dict) -> bool:
    if not user or not user.get("is_executor"):
        return False
    if user.get("is_customer"):
        return user.get("last_role") == ROLE_EXECUTOR
    return True


@router.message(F.text == "Мой профиль")
async def executor_profile(message: Message, db) -> None:
    user = await db.get_user_by_tg_id(message.from_user.id)
    if not _is_executor_context(user):
        return
    profile = await db.get_executor_profile(user["id"])
    text = format_executor_profile(user, profile or {})
    await message.answer(text, reply_markup=profile_executor_keyboard(not user.get("is_customer")))


@router.message(F.text == "Возможные заказы")
async def executor_possible_orders(message: Message, db) -> None:
    user = await db.get_user_by_tg_id(message.from_user.id)
    if not _is_executor_context(user):
        return
    await message.answer("Возможные заказы", reply_markup=possible_orders_keyboard())


@router.message(F.text == "Открытые заказы")
async def executor_open_orders(message: Message, db) -> None:
    user = await db.get_user_by_tg_id(message.from_user.id)
    if not _is_executor_context(user):
        return
    orders = await db.list_orders_for_executor(user["id"])
    if not orders:
        await message.answer("Открытых заказов нет.")
        return
    await message.answer(
        "Ваши открытые заказы:",
        reply_markup=orders_inline(
            orders,
            include_new=False,
            include_back=True,
            prefix="exec_order",
            back_callback="exec_back_main",
            new_callback="exec_order_new",
        ),
    )


@router.message(F.text == "Закрытые заказы")
async def executor_closed_orders(message: Message, db) -> None:
    user = await db.get_user_by_tg_id(message.from_user.id)
    if not _is_executor_context(user):
        return
    orders = await db.list_closed_orders_for_user(user["id"], role="executor")
    order_ids = {o["id"] for o in orders}
    matches = await db.list_matches_for_executor(user["id"])
    for match in matches:
        if match.get("executor_decision") == MATCH_DECISION_DECLINED:
            order = await db.get_order(match["order_id"])
            if order and order["id"] not in order_ids:
                orders.append(order)
                order_ids.add(order["id"])
    if not orders:
        await message.answer("Закрытых заказов нет.")
        return
    await message.answer(
        "Ваши закрытые заказы:",
        reply_markup=orders_inline(
            orders,
            include_new=False,
            include_back=True,
            prefix="exec_order",
            back_callback="exec_back_main",
            new_callback="exec_order_new",
        ),
    )


@router.message(F.text == "Рейтинг")
async def executor_rating(message: Message, db) -> None:
    user = await db.get_user_by_tg_id(message.from_user.id)
    if not _is_executor_context(user):
        return
    avg, cnt = await db.get_rating_summary(user["id"])
    await message.answer(f"Ваш рейтинг: {avg:.2f} (оценок: {cnt})")


@router.message(F.text == "Помощь")
async def executor_help(message: Message, db) -> None:
    user = await db.get_user_by_tg_id(message.from_user.id)
    if not _is_executor_context(user):
        return
    await message.answer("Помощь", reply_markup=help_keyboard())


@router.callback_query(F.data == "become_customer")
async def executor_become_customer(callback: CallbackQuery, db, state) -> None:
    user = await db.get_user_by_tg_id(callback.from_user.id)
    if not user:
        await callback.answer()
        return
    data = {"phone": user.get("phone"), "tg_id": user.get("tg_id")}
    await callback.answer()
    await start_customer_registration(callback.message, state, db, data)


@router.callback_query(F.data == "edit_executor")
async def executor_edit(callback: CallbackQuery, db, state) -> None:
    user = await db.get_user_by_tg_id(callback.from_user.id)
    if not _is_executor_context(user):
        await callback.answer()
        return
    await callback.answer()
    await start_executor_edit(callback.message, state, user["id"])


@router.callback_query(F.data == "exec_back_main")
async def exec_back_main(callback: CallbackQuery, db) -> None:
    user = await db.get_user_by_tg_id(callback.from_user.id)
    if not _is_executor_context(user):
        await callback.answer()
        return
    await callback.answer()
    await show_executor_menu(callback.message, user, db)


@router.callback_query(F.data == "exec_order_back_orders")
async def exec_back_orders(callback: CallbackQuery, db) -> None:
    user = await db.get_user_by_tg_id(callback.from_user.id)
    if not _is_executor_context(user):
        await callback.answer()
        return
    await callback.answer()
    await executor_open_orders(callback.message, db)


@router.callback_query(F.data.startswith("exec_order:"))
async def exec_order_detail(callback: CallbackQuery, db) -> None:
    user = await db.get_user_by_tg_id(callback.from_user.id)
    if not _is_executor_context(user):
        await callback.answer()
        return
    order_id = int(callback.data.split(":", 1)[1])
    order = await db.get_order(order_id)
    if not order:
        await callback.answer("Заказ не найден", show_alert=True)
        return
    customer = await db.get_user_by_id(order["customer_id"])
    text = format_order(order)
    if customer:
        text += f"\nНомер заказчика: {customer.get('phone', '-') }"
    if order.get("status") == ORDER_STATUS_CLOSED:
        await callback.message.answer(
            text,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="Назад", callback_data="exec_back_main")]]
            ),
        )
    else:
        await callback.message.answer(
            text,
            reply_markup=order_actions_keyboard(order_id, for_customer=False, prefix="exec_order"),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("exec_order_close:"))
async def exec_order_close(callback: CallbackQuery, db) -> None:
    order_id = int(callback.data.split(":", 1)[1])
    await callback.message.answer(
        "Вы действительно хотите закрыть заказ?",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Да", callback_data=f"exec_close_yes:{order_id}")],
                [InlineKeyboardButton(text="Назад", callback_data=f"exec_order:{order_id}")],
            ]
        ),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("exec_close_yes:"))
async def exec_close_yes(callback: CallbackQuery, db) -> None:
    user = await db.get_user_by_tg_id(callback.from_user.id)
    if not _is_executor_context(user):
        await callback.answer()
        return
    order_id = int(callback.data.split(":", 1)[1])
    order = await db.get_order(order_id)
    if not order:
        await callback.answer("Заказ не найден", show_alert=True)
        return
    if order.get("assigned_executor_id") and order.get("assigned_executor_id") != user.get("id"):
        await callback.answer("Недостаточно прав", show_alert=True)
        return
    await db.set_order_status(order_id, ORDER_STATUS_CLOSING_BY_EXECUTOR)
    customer = await db.get_user_by_id(order["customer_id"])
    if customer and customer.get("tg_id"):
        await callback.bot.send_message(
            customer["tg_id"],
        f"Добрый день! Исполнитель закрыл заказ {order_id} {html.escape(order.get('name','') or '')}. Подтвердите закрытие.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="Подтвердить закрытие", callback_data=f"cust_close_confirm:{order_id}")]
                ]
            ),
        )
    await callback.message.answer("Ожидайте подтверждение заказчика")
    await callback.answer()


@router.callback_query(F.data == "exec_chosen_list")
async def exec_chosen_list(callback: CallbackQuery, db) -> None:
    user = await db.get_user_by_tg_id(callback.from_user.id)
    if not _is_executor_context(user):
        await callback.answer()
        return
    matches = await db.list_matches_for_executor(user["id"])
    orders = []
    for match in matches:
        if match.get("customer_decision") == MATCH_DECISION_LIKED and not match.get("executor_decision"):
            order = await db.get_order(match["order_id"])
            if order:
                orders.append(order)
    if not orders:
        await callback.message.answer("Нет заказов, где вас выбрали.")
        await callback.answer()
        return
    keyboard = []
    for order in orders:
        label = f"{order['id']} {order.get('name','')}"
        keyboard.append([InlineKeyboardButton(text=label, callback_data=f"exec_chosen_order:{order['id']}")])
    keyboard.append([InlineKeyboardButton(text="Назад", callback_data="exec_back_main")])
    await callback.message.answer("Вас выбрали:", reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
    await callback.answer()


@router.callback_query(F.data.startswith("exec_chosen_order:"))
async def exec_chosen_order(callback: CallbackQuery, db) -> None:
    order_id = int(callback.data.split(":", 1)[1])
    order = await db.get_order(order_id)
    if not order:
        await callback.answer("Заказ не найден", show_alert=True)
        return
    await callback.message.answer(
        format_order(order),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="Да", callback_data=f"exec_chosen_yes:{order_id}"),
                    InlineKeyboardButton(text="Нет", callback_data=f"exec_chosen_no:{order_id}"),
                ],
                [InlineKeyboardButton(text="Назад", callback_data="exec_chosen_list")],
            ]
        ),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("exec_chosen_yes:"))
async def exec_chosen_yes(callback: CallbackQuery, db) -> None:
    user = await db.get_user_by_tg_id(callback.from_user.id)
    order_id = int(callback.data.split(":", 1)[1])
    await db.upsert_match(order_id, user["id"], executor_decision=MATCH_DECISION_LIKED)
    order = await db.get_order(order_id)
    if order:
        customer = await db.get_user_by_id(order["customer_id"])
        if customer and customer.get("tg_id"):
            await callback.bot.send_message(
                customer["tg_id"],
                f"Исполнитель принял заказ {order_id} {html.escape(order.get('name','') or '')}.",
            )
    await callback.message.answer("Заказ принят и добавлен в открытые.")
    await callback.answer()


@router.callback_query(F.data.startswith("exec_chosen_no:"))
async def exec_chosen_no(callback: CallbackQuery, db) -> None:
    user = await db.get_user_by_tg_id(callback.from_user.id)
    order_id = int(callback.data.split(":", 1)[1])
    await db.upsert_match(order_id, user["id"], executor_decision=MATCH_DECISION_DECLINED)
    await callback.message.answer("Заказ отклонен.")
    await callback.answer()


async def _next_order_candidate(executor_id: int, db) -> dict | None:
    profile = await db.get_executor_profile(executor_id)
    if not profile:
        return None
    orders = await db.list_open_orders()
    matches = await db.list_matches_for_executor(executor_id)
    seen = {m["order_id"] for m in matches if m.get("executor_decision")}
    for order in orders:
        if order.get("assigned_executor_id"):
            continue
        if order["customer_id"] == executor_id:
            continue
        if order["id"] in seen:
            continue
        if has_match(order, profile):
            return order
    return None


@router.callback_query(F.data == "exec_match_list")
async def exec_match_list(callback: CallbackQuery, db) -> None:
    user = await db.get_user_by_tg_id(callback.from_user.id)
    if not _is_executor_context(user):
        await callback.answer()
        return
    order = await _next_order_candidate(user["id"], db)
    if not order:
        await callback.message.answer("Доступные заказы закончились")
        await callback.answer()
        return
    await callback.message.answer(
        format_order(order),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="Да", callback_data=f"exec_match_yes:{order['id']}"),
                    InlineKeyboardButton(text="Нет", callback_data=f"exec_match_no:{order['id']}"),
                ],
                [InlineKeyboardButton(text="Назад", callback_data="exec_back_main")],
            ]
        ),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("exec_match_yes:"))
async def exec_match_yes(callback: CallbackQuery, db) -> None:
    user = await db.get_user_by_tg_id(callback.from_user.id)
    order_id = int(callback.data.split(":", 1)[1])
    await db.upsert_match(order_id, user["id"], executor_decision=MATCH_DECISION_LIKED)
    order = await db.get_order(order_id)
    customer = await db.get_user_by_id(order["customer_id"])
    if customer and customer.get("tg_id"):
        await callback.bot.send_message(
            customer["tg_id"],
            f"Исполнитель откликнулся на заказ {order_id} {html.escape(order.get('name','') or '')}.",
        )
    await callback.answer("Отклик отправлен")
    await exec_match_list(callback, db)


@router.callback_query(F.data.startswith("exec_match_no:"))
async def exec_match_no(callback: CallbackQuery, db) -> None:
    user = await db.get_user_by_tg_id(callback.from_user.id)
    order_id = int(callback.data.split(":", 1)[1])
    await db.upsert_match(order_id, user["id"], executor_decision=MATCH_DECISION_DECLINED)
    await callback.answer("Отклонено")
    await exec_match_list(callback, db)


@router.callback_query(F.data.startswith("exec_close_confirm:"))
async def exec_close_confirm(callback: CallbackQuery, db) -> None:
    order_id = int(callback.data.split(":", 1)[1])
    order = await db.get_order(order_id)
    user = await db.get_user_by_tg_id(callback.from_user.id)
    if not order or not user or order.get("assigned_executor_id") != user.get("id"):
        await callback.answer("Недостаточно прав", show_alert=True)
        return
    await db.set_order_status(order_id, ORDER_STATUS_CLOSED)
    await callback.answer("Заказ закрыт")
    if order and order.get("assigned_executor_id"):
        customer = await db.get_user_by_id(order["customer_id"])
        if customer and customer.get("tg_id"):
            await callback.bot.send_message(
                customer["tg_id"],
                "Заказ закрыт. Оцените исполнителя.",
                reply_markup=rating_keyboard(f"rate:{order_id}:{order.get('assigned_executor_id')}"),
            )
    await callback.message.answer("Заказ закрыт.")


@router.callback_query(F.data.startswith("cust_close_confirm:"))
async def cust_close_confirm(callback: CallbackQuery, db) -> None:
    order_id = int(callback.data.split(":", 1)[1])
    order = await db.get_order(order_id)
    user = await db.get_user_by_tg_id(callback.from_user.id)
    if not order or not user or order.get("customer_id") != user.get("id"):
        await callback.answer("Недостаточно прав", show_alert=True)
        return
    await db.set_order_status(order_id, ORDER_STATUS_CLOSED)
    await callback.answer("Заказ закрыт")
    if order:
        executor_id = order.get("assigned_executor_id")
        if executor_id:
            executor = await db.get_user_by_id(executor_id)
            if executor and executor.get("tg_id"):
                await callback.bot.send_message(
                    executor["tg_id"],
                    "Заказ закрыт. Оцените заказчика.",
                    reply_markup=rating_keyboard(f"rate:{order_id}:{order.get('customer_id')}"),
                )
    await callback.message.answer("Заказ закрыт.")
