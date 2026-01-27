from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.types import CallbackQuery, Message


class BlockedMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Any, dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: dict[str, Any],
    ) -> Any:
        db = data.get("db")
        if db is None:
            return await handler(event, data)
        from_user = getattr(event, "from_user", None)
        if not from_user:
            return await handler(event, data)
        user = await db.get_user_by_tg_id(from_user.id)
        if user and user.get("blocked"):
            if isinstance(event, Message):
                await event.answer("Вы заблокированы администрацией.")
                return None
            if isinstance(event, CallbackQuery):
                await event.answer("Вы заблокированы администрацией.", show_alert=True)
                return None
        return await handler(event, data)
