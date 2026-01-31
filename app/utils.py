"""
Утилиты для работы с сообщениями Telegram.
Обеспечивают правильный UX: редактирование вместо спама новыми сообщениями.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import InlineKeyboardMarkup, Message

if TYPE_CHECKING:
    from aiogram.types import CallbackQuery

logger = logging.getLogger(__name__)


async def safe_edit_text(
    message: Message,
    text: str,
    reply_markup: Optional[InlineKeyboardMarkup] = None,
    parse_mode: Optional[str] = None,
) -> Optional[Message]:
    """
    Безопасно редактирует текст сообщения.
    Обрабатывает ошибку MessageNotModified (если текст не изменился).
    
    Returns:
        Отредактированное сообщение или None при ошибке.
    """
    try:
        return await message.edit_text(
            text,
            reply_markup=reply_markup,
            parse_mode=parse_mode,
        )
    except TelegramBadRequest as e:
        if "message is not modified" in str(e).lower():
            # Текст не изменился — это нормально
            return None
        if "message can't be edited" in str(e).lower():
            # Сообщение нельзя редактировать — отправляем новое
            logger.debug("Message can't be edited, sending new one")
            return await message.answer(text, reply_markup=reply_markup, parse_mode=parse_mode)
        raise


async def safe_edit_reply_markup(
    message: Message,
    reply_markup: Optional[InlineKeyboardMarkup] = None,
) -> Optional[Message]:
    """
    Безопасно редактирует только клавиатуру сообщения.
    """
    try:
        return await message.edit_reply_markup(reply_markup=reply_markup)
    except TelegramBadRequest as e:
        if "message is not modified" in str(e).lower():
            return None
        raise


async def safe_delete(message: Message) -> bool:
    """
    Безопасно удаляет сообщение.
    Игнорирует ошибки если сообщение уже удалено или слишком старое.
    
    Returns:
        True если удалено успешно, False при ошибке.
    """
    try:
        await message.delete()
        return True
    except TelegramBadRequest as e:
        error_msg = str(e).lower()
        if "message to delete not found" in error_msg:
            return False
        if "message can't be deleted" in error_msg:
            return False
        raise


async def edit_or_send(
    message: Message,
    text: str,
    reply_markup: Optional[InlineKeyboardMarkup] = None,
    parse_mode: Optional[str] = None,
) -> Message:
    """
    Пытается отредактировать сообщение, если не получается — отправляет новое.
    Универсальный метод для callback-хендлеров.
    """
    try:
        result = await message.edit_text(
            text,
            reply_markup=reply_markup,
            parse_mode=parse_mode,
        )
        if result:
            return result
    except TelegramBadRequest:
        pass
    
    # Если редактирование не удалось — отправляем новое
    return await message.answer(text, reply_markup=reply_markup, parse_mode=parse_mode)


async def callback_edit_text(
    callback: "CallbackQuery",
    text: str,
    reply_markup: Optional[InlineKeyboardMarkup] = None,
    parse_mode: Optional[str] = None,
    answer_callback: bool = True,
) -> Optional[Message]:
    """
    Редактирует сообщение из callback и отвечает на callback.
    Основной метод для всех callback-хендлеров.
    
    Args:
        callback: CallbackQuery объект
        text: Новый текст сообщения
        reply_markup: Новая inline-клавиатура
        parse_mode: Режим парсинга (HTML, Markdown)
        answer_callback: Отвечать ли на callback (по умолчанию True)
    """
    if answer_callback:
        await callback.answer()
    
    return await safe_edit_text(
        callback.message,
        text,
        reply_markup=reply_markup,
        parse_mode=parse_mode,
    )
