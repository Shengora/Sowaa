from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database.models import Client, User, Case
from bot.services.case import CaseService
from sqlalchemy import select

router = Router()

@router.message(Command("mycases"))
async def my_cases(message: Message, _, db_user: User, session: AsyncSession):
    if not db_user or db_user.role.value != "client":
        return

    stmt = select(Client).where(Client.user_id == db_user.id)
    result = await session.execute(stmt)
    client = result.scalar_one_or_none()

    if not client:
        return await message.answer(_("no_lawyer_assigned"))

    cases = await CaseService.get_client_cases(session, client.id)

    if not cases:
        return await message.answer(_("no_cases"))

    text = _("your_cases") + "\n\n"
    for case in cases:
        text += f"ID: {case.id} | {case.title} | Status: {case.status.value}\n"

    await message.answer(text)