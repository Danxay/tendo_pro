from __future__ import annotations

import html
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


def _e(text: str | None) -> str:
    """Helper to escape text."""
    if text is None:
        return ""
    return html.escape(str(text))


def _fmt_list(items: list[str]) -> str:
    if not items:
        return "-"
    return ", ".join([_e(i) for i in items])


def format_order(order: dict[str, Any]) -> str:
    lines = [
        f"Номер заказа: {order['id']}",
        f"Наименование заказа: {_e(order.get('name')) or '-'}",
        f"Вид документации: {_fmt_list(order.get('doc_types', []))}",
        f"Вид строительства: {_fmt_list(order.get('construction_types', []))}",
    ]
    if order.get("sections_capital"):
        lines.append(f"Разделы (кап. строительство): {_fmt_list(order.get('sections_capital', []))}")
    if order.get("sections_linear"):
        lines.append(f"Разделы (линейные объекты): {_fmt_list(order.get('sections_linear', []))}")
    lines.extend(
        [
            f"Описание: {_e(order.get('description')) or '-'}",
            f"Срок исполнения: {_e(order.get('deadline')) or '-'}",
            f"Цена: {_e(order.get('price')) or '-'}",
            f"Экспертиза: {'да' if order.get('expertise_required') else 'нет'}",
            f"Файлы: {_e(order.get('files_link')) or '-'}",
        ]
    )
    return "\n".join(lines)


def format_executor_card(executor: dict[str, Any]) -> str:
    lines = [
        f"Имя: {_e(executor.get('first_name')) or '-'}",
        f"Опыт: {_e(executor.get('experience')) or '-'}",
        f"Вид строительства: {_fmt_list(executor.get('construction_types', []))}",
    ]
    if executor.get("sections_capital"):
        lines.append(f"Разделы (кап. строительство): {_fmt_list(executor.get('sections_capital', []))}")
    if executor.get("sections_linear"):
        lines.append(f"Разделы (линейные объекты): {_fmt_list(executor.get('sections_linear', []))}")
    if executor.get("resume_link"):
        lines.append(f"Резюме (ссылка): {_e(executor.get('resume_link'))}")
    if executor.get("resume_text"):
        lines.append(f"Резюме: {_e(executor.get('resume_text'))}")
    return "\n".join(lines)


def format_customer_profile(user: dict[str, Any]) -> str:
    lines = [
        "Роль в системе: Заказчик",
        f"Имя Фамилия: {_e(user.get('first_name')) or '-'} {_e(user.get('last_name')) or '-'}",
    ]
    if user.get("org_name"):
        lines.append(f"Наименование организации: {_e(user.get('org_name'))}")
    return "\n".join(lines)


def format_executor_profile(user: dict[str, Any], profile: dict[str, Any]) -> str:
    lines = [
        "Роль в системе: Исполнитель",
        f"Имя Фамилия: {_e(user.get('first_name')) or '-'} {_e(user.get('last_name')) or '-'}",
        f"Опыт работы: {_e(profile.get('experience')) or '-'}",
    ]
    if profile.get("resume_link"):
        lines.append(f"Резюме (ссылка): {_e(profile.get('resume_link'))}")
    if profile.get("resume_text"):
        lines.append(f"Резюме: {_e(profile.get('resume_text'))}")
    if user.get("org_name"):
        lines.append(f"Наименование организации: {_e(user.get('org_name'))}")
    return "\n".join(lines)
