from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from sqlalchemy import select
from bot.database.models import User, Lawyer, Client, Role
from sqlalchemy.ext.asyncio import AsyncSession

router = Router()

@router.message(CommandStart())
async def start_cmd(message: Message, _, session: AsyncSession):
    args = message.text.split(maxsplit=1)

    if len(args) < 2:
        return await message.answer(_("start_no_token"))

    token = args[1]

    # Check token
    stmt = select(Lawyer).where(Lawyer.invite_token == token)
    result = await session.execute(stmt)
    lawyer = result.scalar_one_or_none()

    if not lawyer:
        return await message.answer(_("start_invalid_token"))

    # Ensure user exists
    stmt = select(User).where(User.telegram_id == message.from_user.id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            telegram_id=message.from_user.id,
            role=Role.client
        )
        session.add(user)
        await session.flush()

    # Ensure client mapping exists
    stmt = select(Client).where(Client.user_id == user.id)
    result = await session.execute(stmt)
    client = result.scalar_one_or_none()

    if not client:
        client = Client(
            user_id=user.id,
            lawyer_id=lawyer.id
        )
        session.add(client)
        # Flush to get client ID if needed, though commit happens in middleware
        await session.flush()
    else:
        # Client already registered
        pass

    await message.answer(_("start_success"))