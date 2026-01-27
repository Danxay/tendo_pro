from __future__ import annotations

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)


def start_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Запустить")]],
        resize_keyboard=True,
    )


def contact_keyboard(label: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=label, request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def role_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Заказчик"), KeyboardButton(text="Исполнитель")]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def customer_main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Мой профиль")],
            [KeyboardButton(text="Открытые заказы"), KeyboardButton(text="Закрытые заказы")],
            [KeyboardButton(text="Рейтинг"), KeyboardButton(text="Помощь")],
        ],
        resize_keyboard=True,
    )


def executor_main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Мой профиль")],
            [KeyboardButton(text="Возможные заказы")],
            [KeyboardButton(text="Открытые заказы"), KeyboardButton(text="Закрытые заказы")],
            [KeyboardButton(text="Рейтинг"), KeyboardButton(text="Помощь")],
        ],
        resize_keyboard=True,
    )


def admin_main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Отчет по заказчикам")],
            [KeyboardButton(text="Отчет по исполнителям")],
            [KeyboardButton(text="Отчет по принятым двум сторонами заказами")],
            [KeyboardButton(text="Статистика бота")],
        ],
        resize_keyboard=True,
    )


def profile_customer_keyboard(can_become_executor: bool) -> InlineKeyboardMarkup:
    buttons = []
    if can_become_executor:
        buttons.append([InlineKeyboardButton(text="Стать исполнителем", callback_data="become_executor")])
    buttons.append([InlineKeyboardButton(text="Назад", callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def profile_executor_keyboard(can_become_customer: bool) -> InlineKeyboardMarkup:
    buttons = []
    if can_become_customer:
        buttons.append([InlineKeyboardButton(text="Стать заказчиком", callback_data="become_customer")])
    buttons.append([InlineKeyboardButton(text="Редактировать", callback_data="edit_executor")])
    buttons.append([InlineKeyboardButton(text="Назад", callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def orders_inline(
    orders: list[dict],
    include_new: bool,
    include_back: bool,
    prefix: str,
    back_callback: str,
    new_callback: str,
) -> InlineKeyboardMarkup:
    keyboard = []
    for order in orders:
        label = f"{order['id']} {order.get('name', '')}".strip()
        keyboard.append([InlineKeyboardButton(text=label, callback_data=f"{prefix}:{order['id']}")])
    if include_new:
        keyboard.append([InlineKeyboardButton(text="Новый заказ", callback_data=new_callback)])
    if include_back:
        keyboard.append([InlineKeyboardButton(text="Назад", callback_data=back_callback)])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def order_actions_keyboard(order_id: int, for_customer: bool, prefix: str) -> InlineKeyboardMarkup:
    buttons = []
    if for_customer:
        buttons.extend(
            [
                [InlineKeyboardButton(text="Редактировать", callback_data=f"{prefix}_edit:{order_id}")],
                [InlineKeyboardButton(text="Отклики", callback_data=f"{prefix}_responses:{order_id}")],
                [InlineKeyboardButton(text="Закрыть заказ", callback_data=f"{prefix}_close:{order_id}")],
            ]
        )
    else:
        buttons.extend(
            [
                [InlineKeyboardButton(text="Закрыть заказ", callback_data=f"{prefix}_close:{order_id}")],
            ]
        )
    buttons.append([InlineKeyboardButton(text="Назад", callback_data=f"{prefix}_back_orders")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def responses_menu_keyboard(order_id: int, prefix: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Новые", callback_data=f"{prefix}_responses_new:{order_id}")],
            [InlineKeyboardButton(text="Принятые", callback_data=f"{prefix}_responses_liked:{order_id}")],
            [InlineKeyboardButton(text="Отказанные", callback_data=f"{prefix}_responses_declined:{order_id}")],
            [InlineKeyboardButton(text="Назад", callback_data=f"{prefix}:{order_id}")],
        ]
    )


def yes_no_keyboard(prefix: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Да", callback_data=f"{prefix}:yes"),
                InlineKeyboardButton(text="Нет", callback_data=f"{prefix}:no"),
            ],
            [InlineKeyboardButton(text="Назад", callback_data="back")],
        ]
    )


def multiselect_keyboard(options: list[str], selected_indices: set[int]) -> InlineKeyboardMarkup:
    keyboard = []
    for idx, opt in enumerate(options):
        label = f"✅ {opt}" if idx in selected_indices else f"◻️ {opt}"
        keyboard.append([InlineKeyboardButton(text=label, callback_data=f"multi:{idx}")])
    keyboard.append([InlineKeyboardButton(text="Готово", callback_data="multi_done")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def possible_orders_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Вас выбрали", callback_data="exec_chosen_list")],
            [InlineKeyboardButton(text="Подбор", callback_data="exec_match_list")],
            [InlineKeyboardButton(text="Назад", callback_data="exec_back_main")],
        ]
    )


def help_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Новое сообщение", callback_data="help_new")],
            [InlineKeyboardButton(text="Назад", callback_data="back_main")],
        ]
    )


def accept_decline_keyboard(prefix: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Да", callback_data=f"{prefix}:yes"),
                InlineKeyboardButton(text="Нет", callback_data=f"{prefix}:no"),
            ],
            [InlineKeyboardButton(text="Назад", callback_data="back")],
        ]
    )


def confirm_keyboard(action: str, back_action: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Да", callback_data=action)],
            [InlineKeyboardButton(text="Назад", callback_data=back_action)],
        ]
    )


def rating_keyboard(prefix: str) -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(text="⭐" * stars, callback_data=f"{prefix}:{stars}")
        for stars in range(1, 6)
    ]
    return InlineKeyboardMarkup(inline_keyboard=[[btn] for btn in buttons])
