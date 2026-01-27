from __future__ import annotations

from typing import Any

from .constants import CONSTRUCTION_TYPES


def has_match(order: dict[str, Any], executor: dict[str, Any]) -> bool:
    order_types = set(order.get("construction_types", []))
    executor_types = set(executor.get("construction_types", []))
    common_types = order_types & executor_types
    for ctype in common_types:
        if ctype == CONSTRUCTION_TYPES[0]:
            if set(order.get("sections_capital", [])) & set(executor.get("sections_capital", [])):
                return True
        if ctype == CONSTRUCTION_TYPES[1]:
            if set(order.get("sections_linear", [])) & set(executor.get("sections_linear", [])):
                return True
    return False


def _fmt_list(items: list[str]) -> str:
    if not items:
        return "-"
    return ", ".join(items)


def format_order(order: dict[str, Any]) -> str:
    lines = [
        f"Номер заказа: {order['id']}",
        f"Наименование заказа: {order.get('name', '-')}",
        f"Вид документации: {_fmt_list(order.get('doc_types', []))}",
        f"Вид строительства: {_fmt_list(order.get('construction_types', []))}",
    ]
    if order.get("sections_capital"):
        lines.append(f"Разделы (кап. строительство): {_fmt_list(order.get('sections_capital', []))}")
    if order.get("sections_linear"):
        lines.append(f"Разделы (линейные объекты): {_fmt_list(order.get('sections_linear', []))}")
    lines.extend(
        [
            f"Описание: {order.get('description') or '-'}",
            f"Срок исполнения: {order.get('deadline') or '-'}",
            f"Цена: {order.get('price') or '-'}",
            f"Экспертиза: {'да' if order.get('expertise_required') else 'нет'}",
            f"Файлы: {order.get('files_link') or '-'}",
        ]
    )
    return "\n".join(lines)


def format_executor_card(executor: dict[str, Any]) -> str:
    lines = [
        f"Имя: {executor.get('first_name', '-')}",
        f"Опыт: {executor.get('experience', '-')}",
        f"Вид строительства: {_fmt_list(executor.get('construction_types', []))}",
    ]
    if executor.get("sections_capital"):
        lines.append(f"Разделы (кап. строительство): {_fmt_list(executor.get('sections_capital', []))}")
    if executor.get("sections_linear"):
        lines.append(f"Разделы (линейные объекты): {_fmt_list(executor.get('sections_linear', []))}")
    if executor.get("resume_link"):
        lines.append(f"Резюме (ссылка): {executor.get('resume_link')}")
    if executor.get("resume_text"):
        lines.append(f"Резюме: {executor.get('resume_text')}")
    return "\n".join(lines)


def format_customer_profile(user: dict[str, Any]) -> str:
    lines = [
        "Роль в системе: Заказчик",
        f"Имя Фамилия: {user.get('first_name', '-') } {user.get('last_name', '-')}",
    ]
    if user.get("org_name"):
        lines.append(f"Наименование организации: {user.get('org_name')}")
    return "\n".join(lines)


def format_executor_profile(user: dict[str, Any], profile: dict[str, Any]) -> str:
    lines = [
        "Роль в системе: Исполнитель",
        f"Имя Фамилия: {user.get('first_name', '-') } {user.get('last_name', '-')}",
        f"Опыт работы: {profile.get('experience', '-')}",
    ]
    if profile.get("resume_link"):
        lines.append(f"Резюме (ссылка): {profile.get('resume_link')}")
    if profile.get("resume_text"):
        lines.append(f"Резюме: {profile.get('resume_text')}")
    if user.get("org_name"):
        lines.append(f"Наименование организации: {user.get('org_name')}")
    return "\n".join(lines)
