from bot.config import config
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database.models import User, Lawyer, Subscription, Role
from sqlalchemy import select
from datetime import datetime, timedelta
import secrets

router = Router()

def is_admin(user_id: int) -> bool:
    return user_id in config.parsed_admin_ids

@router.message(Command("add_lawyer"))
async def add_lawyer(message: Message, _, session: AsyncSession):
    if not is_admin(message.from_user.id):
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        return await message.answer(_("admin_usage_add_lawyer"))

    try:
        tg_id = int(args[1])
    except ValueError:
        return await message.answer(_("admin_invalid_id"))

    # Check if user exists
    stmt = select(User).where(User.telegram_id == tg_id)
    user = (await session.execute(stmt)).scalar_one_or_none()

    if not user:
        user = User(telegram_id=tg_id, role=Role.lawyer)
        session.add(user)
        await session.flush()
    else:
        user.role = Role.lawyer
        await session.flush()

    # Check if lawyer exists
    stmt = select(Lawyer).where(Lawyer.user_id == user.id)
    lawyer = (await session.execute(stmt)).scalar_one_or_none()

    if not lawyer:
        token = secrets.token_urlsafe(16)
        lawyer = Lawyer(user_id=user.id, invite_token=token)
        session.add(lawyer)
        await session.flush()

        # Add 14 days trial
        sub = Subscription(
            lawyer_id=lawyer.id,
            plan_name="trial",
            active_until=datetime.utcnow() + timedelta(days=14)
        )
        session.add(sub)

        await message.answer(_("admin_lawyer_added", tg_id=tg_id))
    else:
        await message.answer(_("admin_lawyer_already_exists"))

@router.message(Command("remove_lawyer"))
async def remove_lawyer(message: Message, _, session: AsyncSession):
    if not is_admin(message.from_user.id):
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        return await message.answer(_("admin_usage_remove_lawyer"))

    try:
        tg_id = int(args[1])
    except ValueError:
        return await message.answer(_("admin_invalid_id"))

    stmt = select(User).where(User.telegram_id == tg_id)
    user = (await session.execute(stmt)).scalar_one_or_none()

    if user and user.role == Role.lawyer:
        user.role = Role.client
        await message.answer(_("admin_lawyer_removed", tg_id=tg_id))
    else:
        await message.answer(_("admin_not_lawyer"))

@router.message(Command("stats"))
async def stats(message: Message, _, session: AsyncSession):
    if not is_admin(message.from_user.id):
        return

    from bot.database.models import Client, GeneratedDocument, Case
    from sqlalchemy import func

    lawyers_c = (await session.execute(select(func.count(Lawyer.id)))).scalar()
    clients_c = (await session.execute(select(func.count(Client.id)))).scalar()
    cases_c = (await session.execute(select(func.count(Case.id)))).scalar()
    docs_c = (await session.execute(select(func.count(GeneratedDocument.id)))).scalar()

    text = _("admin_stats", lawyers=lawyers_c, clients=clients_c, cases=cases_c, docs=docs_c)
    await message.answer(text)