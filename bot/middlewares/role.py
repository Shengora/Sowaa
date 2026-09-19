from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy import select
from bot.database.models import User

class RoleMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        telegram_user = data.get("event_from_user")
        session = data.get("session")
        if not telegram_user or not session:
            return await handler(event, data)

        stmt = select(User).where(User.telegram_id == telegram_user.id)
        result = await session.execute(stmt)
        db_user = result.scalar_one_or_none()

        # Pass user to the handler
        data["db_user"] = db_user

        return await handler(event, data)