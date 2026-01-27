import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.callback_answer import CallbackAnswerMiddleware

from .config import load_config
from .db import Database
from .handlers import admin, customer, executor, help as help_handlers, navigation, ratings, registration, start
from .middleware import BlockedMiddleware


async def main() -> None:
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    config = load_config()

    os.makedirs(os.path.dirname(config.db_path), exist_ok=True)
    db = Database(config.db_path)
    await db.init()
    await db.seed_admin_whitelist(config.admin_phones)

    bot = Bot(token=config.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())

    dp["db"] = db
    dp["config"] = config

    dp.message.middleware(BlockedMiddleware())
    dp.callback_query.middleware(BlockedMiddleware())
    dp.callback_query.middleware(CallbackAnswerMiddleware())

    dp.include_router(start.router)
    dp.include_router(registration.router)
    dp.include_router(customer.router)
    dp.include_router(executor.router)
    dp.include_router(admin.router)
    dp.include_router(help_handlers.router)
    dp.include_router(navigation.router)
    dp.include_router(ratings.router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
