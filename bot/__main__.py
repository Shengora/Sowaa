import asyncio
import logging
from aiogram import Bot, Dispatcher
from bot.config import config
from bot.handlers.start import router as start_router
from bot.middlewares.role import RoleMiddleware
from bot.middlewares.i18n import I18nMiddleware
from bot.database.core import engine, Base

logging.basicConfig(level=logging.INFO)

async def main():
    bot = Bot(token=config.bot_token)
    dp = Dispatcher()

    # Create tables if not using alembic directly in tests/dev, but we rely on alembic.
    # Just to ensure tests with aiosqlite can run if needed.
    if config.database_url.startswith("sqlite"):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    # Middlewares
    from bot.middlewares.db import DbSessionMiddleware
    from bot.database.core import async_session
    dp.update.middleware(DbSessionMiddleware(async_session))

    dp.update.middleware(I18nMiddleware("bot/locales"))
    dp.update.middleware(RoleMiddleware())

    from bot.middlewares.subscription import SubscriptionMiddleware
    dp.update.middleware(SubscriptionMiddleware())

    # Routers
    from bot.handlers.client.document import router as document_router
    from bot.handlers.client.cases import router as client_cases_router
    from bot.handlers.admin import router as admin_router
    from bot.handlers.lawyer import router as lawyer_router
    dp.include_router(start_router)
    dp.include_router(document_router)
    dp.include_router(client_cases_router)
    dp.include_router(admin_router)
    dp.include_router(lawyer_router)

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())