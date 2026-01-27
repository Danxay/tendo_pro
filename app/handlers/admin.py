from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, Message

from ..constants import MATCH_DECISION_LIKED, ORDER_STATUS_CLOSED
from ..excel import build_xlsx
from ..services import has_match
from ..validation import normalize_phone

router = Router()


def _is_admin(user: dict) -> bool:
    return bool(user and user.get("is_admin"))


def _full_name(user: dict) -> str:
    return f"{user.get('first_name','')} {user.get('last_name','')}".strip()


@router.message(Command("admin_add"))
async def admin_add(message: Message, db) -> None:
    user = await db.get_user_by_tg_id(message.from_user.id)
    if not _is_admin(user):
        return
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer("Использование: /admin_add +79991234567")
        return
    phone = normalize_phone(parts[1])
    if not phone:
        await message.answer("Неверный номер")
        return
    await db.add_admin_phone(phone)
    await message.answer("Администратор добавлен")


@router.message(Command("admin_remove"))
async def admin_remove(message: Message, db) -> None:
    user = await db.get_user_by_tg_id(message.from_user.id)
    if not _is_admin(user):
        return
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer("Использование: /admin_remove +79991234567")
        return
    phone = normalize_phone(parts[1])
    await db.remove_admin_phone(phone)
    await message.answer("Администратор удален")


@router.message(Command("block"))
async def admin_block(message: Message, db) -> None:
    user = await db.get_user_by_tg_id(message.from_user.id)
    if not _is_admin(user):
        return
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer("Использование: /block +79991234567")
        return
    phone = normalize_phone(parts[1])
    target = await db.get_user_by_phone(phone)
    if not target:
        await message.answer("Пользователь не найден")
        return
    await db.set_blocked(target["id"], True)
    await message.answer("Пользователь заблокирован")


@router.message(Command("unblock"))
async def admin_unblock(message: Message, db) -> None:
    user = await db.get_user_by_tg_id(message.from_user.id)
    if not _is_admin(user):
        return
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer("Использование: /unblock +79991234567")
        return
    phone = normalize_phone(parts[1])
    target = await db.get_user_by_phone(phone)
    if not target:
        await message.answer("Пользователь не найден")
        return
    await db.set_blocked(target["id"], False)
    await message.answer("Пользователь разблокирован")


@router.message(Command("reviews"))
async def admin_reviews(message: Message, db) -> None:
    user = await db.get_user_by_tg_id(message.from_user.id)
    if not _is_admin(user):
        return
    ratings = await db.fetchall("SELECT * FROM ratings")
    rows = [["№", "Заказ", "От кого", "Кому", "Оценка", "Отзыв", "Дата"]]
    idx = 1
    for rating in ratings:
        from_user = await db.get_user_by_id(rating["from_user_id"]) or {}
        to_user = await db.get_user_by_id(rating["to_user_id"]) or {}
        rows.append(
            [
                str(idx),
                str(rating.get("order_id")),
                f"{from_user.get('phone','')} {_full_name(from_user)}",
                f"{to_user.get('phone','')} {_full_name(to_user)}",
                str(rating.get("stars")),
                rating.get("review") or "",
                rating.get("created_at") or "",
            ]
        )
        idx += 1
    data = build_xlsx(rows, sheet_name="Reviews")
    await message.answer_document(BufferedInputFile(data, filename="reviews.xlsx"))


@router.message(F.text == "Отчет по заказчикам")
async def report_customers(message: Message, db) -> None:
    user = await db.get_user_by_tg_id(message.from_user.id)
    if not _is_admin(user):
        return
    customers = await db.list_customers()
    rows = [
        [
            "№",
            "Номер телефона",
            "Имя Фамилия",
            "Количество заказов",
            "Открытые заказы (исполнитель)",
            "Количество закрытых заказов",
            "Количество исполнителей и разделы по заказу",
            "Рейтинг",
        ]
    ]
    for idx, customer in enumerate(customers, start=1):
        orders = await db.list_orders_by_customer(customer["id"])
        open_orders = [o for o in orders if o["status"] != ORDER_STATUS_CLOSED]
        closed_orders = [o for o in orders if o["status"] == ORDER_STATUS_CLOSED]
        open_info = []
        for order in open_orders:
            if order.get("assigned_executor_id"):
                executor = await db.get_user_by_id(order["assigned_executor_id"])
                open_info.append(
                    f"#{order['id']}: {executor.get('phone','-')} {_full_name(executor)}"
                )
            else:
                open_info.append(f"#{order['id']}: исполнитель не подтвержден")
        execs_info = []
        for order in orders:
            matches = await db.list_matches_for_order(order["id"])
            exec_count = len({m["executor_id"] for m in matches if m.get("customer_decision") == MATCH_DECISION_LIKED})
            sections = ", ".join(order.get("sections_capital", []) + order.get("sections_linear", []))
            execs_info.append(f"#{order['id']}: {exec_count}, разделы: {sections}")
        avg, cnt = await db.get_rating_summary(customer["id"])
        rows.append(
            [
                str(idx),
                customer.get("phone", ""),
                _full_name(customer),
                str(len(orders)),
                "; ".join(open_info),
                str(len(closed_orders)),
                "; ".join(execs_info),
                f"{avg:.2f} ({cnt})",
            ]
        )
    data = build_xlsx(rows, sheet_name="Customers")
    await message.answer_document(BufferedInputFile(data, filename="customers_report.xlsx"))


@router.message(F.text == "Отчет по исполнителям")
async def report_executors(message: Message, db) -> None:
    user = await db.get_user_by_tg_id(message.from_user.id)
    if not _is_admin(user):
        return
    executors = await db.list_executors()
    orders = await db.list_open_orders()
    rows = [
        [
            "№",
            "Номер телефона",
            "Имя Фамилия",
            "Разрабатываемые разделы",
            "Количество принятых заказов",
            "Количество возможных заказов",
            "Открытые заказы (заказчик)",
            "Количество выполненных заказов",
            "Рейтинг",
        ]
    ]
    for idx, executor in enumerate(executors, start=1):
        profile = await db.get_executor_profile(executor["id"])
        matches = await db.list_matches_for_executor(executor["id"])
        accepted = [m for m in matches if m.get("customer_decision") == MATCH_DECISION_LIKED and m.get("executor_decision") == MATCH_DECISION_LIKED]
        possible = [o for o in orders if not o.get("assigned_executor_id") and profile and has_match(o, profile)]
        open_orders = []
        for match in accepted:
            order = await db.get_order(match["order_id"])
            if order and order["status"] != ORDER_STATUS_CLOSED:
                customer = await db.get_user_by_id(order["customer_id"])
                open_orders.append(f"#{order['id']}: {customer.get('phone','-')} {_full_name(customer)}")
        closed_orders = await db.list_closed_orders_for_user(executor["id"], role="executor")
        avg, cnt = await db.get_rating_summary(executor["id"])
        sections = ", ".join(
            (profile or {}).get("sections_capital", []) + (profile or {}).get("sections_linear", [])
        )
        rows.append(
            [
                str(idx),
                executor.get("phone", ""),
                _full_name(executor),
                sections,
                str(len(accepted)),
                str(len(possible)),
                "; ".join(open_orders),
                str(len(closed_orders)),
                f"{avg:.2f} ({cnt})",
            ]
        )
    data = build_xlsx(rows, sheet_name="Executors")
    await message.answer_document(BufferedInputFile(data, filename="executors_report.xlsx"))


@router.message(F.text == "Отчет по принятым двум сторонами заказами")
async def report_mutual(message: Message, db) -> None:
    user = await db.get_user_by_tg_id(message.from_user.id)
    if not _is_admin(user):
        return
    matches = await db.fetchall(
        "SELECT * FROM matches WHERE customer_decision = ? AND executor_decision = ?",
        (MATCH_DECISION_LIKED, MATCH_DECISION_LIKED),
    )
    rows = [["№", "Телефон заказчика", "Имя заказчика", "Телефон исполнителя", "Имя исполнителя", "Срок"]]
    idx = 1
    for match in matches:
        order = await db.get_order(match["order_id"])
        if not order:
            continue
        customer = await db.get_user_by_id(order["customer_id"])
        executor = await db.get_user_by_id(match["executor_id"])
        rows.append(
            [
                str(idx),
                customer.get("phone", ""),
                _full_name(customer),
                executor.get("phone", ""),
                _full_name(executor),
                order.get("deadline", ""),
            ]
        )
        idx += 1
    data = build_xlsx(rows, sheet_name="Mutual")
    await message.answer_document(BufferedInputFile(data, filename="mutual_orders.xlsx"))


@router.message(F.text == "Статистика бота")
async def report_stats(message: Message, db) -> None:
    user = await db.get_user_by_tg_id(message.from_user.id)
    if not _is_admin(user):
        return
    stats = await db.count_stats()
    rows = [
        [
            "Количество пользователей",
            "Количество заказчиков",
            "Количество исполнителей",
            "Количество заказов",
            "Количество заказов в работе",
        ],
        [
            str(stats["users"]),
            str(stats["customers"]),
            str(stats["executors"]),
            str(stats["orders"]),
            str(stats["in_work"]),
        ],
    ]
    data = build_xlsx(rows, sheet_name="Stats")
    await message.answer_document(BufferedInputFile(data, filename="bot_stats.xlsx"))
