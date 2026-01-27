from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from ..states import RatingState

router = Router()


@router.callback_query(F.data.startswith("rate:"))
async def rate_callback(callback: CallbackQuery, state: FSMContext) -> None:
    parts = callback.data.split(":")
    if len(parts) != 4:
        await callback.answer()
        return
    _, order_id, to_user_id, stars = parts
    await state.update_data(
        rating_order_id=int(order_id),
        rating_to_user_id=int(to_user_id),
        rating_stars=int(stars),
    )
    await state.set_state(RatingState.waiting_review)
    await callback.message.answer("Напишите отзыв или отправьте '-' чтобы пропустить")
    await callback.answer()


@router.message(RatingState.waiting_review)
async def rate_review(message: Message, state: FSMContext, db) -> None:
    data = await state.get_data()
    review = (message.text or "").strip()
    if review == "-":
        review = None
    user = await db.get_user_by_tg_id(message.from_user.id)
    if not user:
        await message.answer("Пользователь не найден.")
        await state.clear()
        return
    await db.add_rating(
        data.get("rating_order_id"),
        user["id"],
        data.get("rating_to_user_id"),
        data.get("rating_stars"),
        review,
    )
    await message.answer("Спасибо за оценку!")
    await state.clear()
