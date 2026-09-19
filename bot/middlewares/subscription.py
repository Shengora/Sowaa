from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from aiogram.types.message import Message
from aiogram.types.callback_query import CallbackQuery
from sqlalchemy import select
from bot.database.models import User, Lawyer, Subscription
from datetime import datetime

class SubscriptionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        db_user: User | None = data.get("db_user")
        _ = data.get("_")

        if db_user and db_user.role.value == "lawyer":
            # For simplicity, we check if the user triggered a lawyer handler
            # In a real app we'd map handlers, but here we can check the command or state
            is_lawyer_action = False

            if isinstance(event, Message) and event.text and event.text.startswith("/lawyer"):
                is_lawyer_action = True
            elif isinstance(event, CallbackQuery) and event.data and event.data.startswith("lawyer_"):
                is_lawyer_action = True

            if is_lawyer_action:
                session = data.get("session")
                if session:
                    stmt = select(Lawyer).where(Lawyer.user_id == db_user.id)
                    lawyer = (await session.execute(stmt)).scalar_one_or_none()
                    if lawyer:
                        stmt = select(Subscription).where(Subscription.lawyer_id == lawyer.id).order_by(Subscription.id.desc()).limit(1)
                        sub = (await session.execute(stmt)).scalar_one_or_none()

                        if not sub or sub.active_until < datetime.utcnow():
                            msg = _("subscription_expired") if _ else "Subscription expired. Restricting features."

                            if hasattr(event, "answer"):
                                if isinstance(event, CallbackQuery):
                                    await event.answer(msg, show_alert=True)
                                else:
                                    await event.answer(msg)
                            return None

        return await handler(event, data)