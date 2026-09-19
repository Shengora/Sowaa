from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from bot.database.models import User, Lawyer, Client, Case, DocumentTemplate, CaseStatus
from bot.services.case import CaseService
from sqlalchemy import select
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

router = Router()

class LawyerStates(StatesGroup):
    changing_status = State()
    adding_note = State()

def lawyer_main_keyboard(_):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=_("btn_my_clients"), callback_data="lawyer_clients")],
        [InlineKeyboardButton(text=_("btn_my_cases"), callback_data="lawyer_cases")],
        [InlineKeyboardButton(text=_("btn_my_templates"), callback_data="lawyer_templates")],
        [InlineKeyboardButton(text=_("btn_my_link"), callback_data="lawyer_link")]
    ])

@router.message(Command("lawyer"))
async def lawyer_menu(message: Message, _, db_user: User):
    if not db_user or db_user.role.value != "lawyer":
        return

    await message.answer(_("lawyer_panel"), reply_markup=lawyer_main_keyboard(_))

@router.callback_query(F.data == "lawyer_link")
async def lawyer_link(callback: CallbackQuery, _, db_user: User, session: AsyncSession):
    stmt = select(Lawyer).where(Lawyer.user_id == db_user.id)
    lawyer = (await session.execute(stmt)).scalar_one()
    bot_username = (await callback.bot.me()).username

    link = f"https://t.me/{bot_username}?start={lawyer.invite_token}"
    await callback.message.edit_text(_("lawyer_link_text", link=link), reply_markup=lawyer_main_keyboard(_))

@router.callback_query(F.data == "lawyer_clients")
async def lawyer_clients(callback: CallbackQuery, _, db_user: User, session: AsyncSession):
    stmt = select(Lawyer).where(Lawyer.user_id == db_user.id)
    lawyer = (await session.execute(stmt)).scalar_one()

    stmt = select(Client).where(Client.lawyer_id == lawyer.id)
    clients = (await session.execute(stmt)).scalars().all()

    if not clients:
        text = _("lawyer_no_clients")
    else:
        text = _("lawyer_clients_list") + "\n"
        for c in clients:
            text += f"- ID: {c.id}\n"

    await callback.message.edit_text(text, reply_markup=lawyer_main_keyboard(_))

@router.callback_query(F.data == "lawyer_cases")
async def lawyer_cases(callback: CallbackQuery, _, db_user: User, session: AsyncSession):
    stmt = select(Lawyer).where(Lawyer.user_id == db_user.id)
    lawyer = (await session.execute(stmt)).scalar_one()

    cases = await CaseService.get_lawyer_cases(session, lawyer.id)

    if not cases:
        text = _("lawyer_no_cases")
        await callback.message.edit_text(text, reply_markup=lawyer_main_keyboard(_))
        return

    text = _("lawyer_cases_list") + "\n"
    kb = []
    for c in cases:
        text += f"ID: {c.id} | {c.title} | {c.status.value}\n"
        kb.append([InlineKeyboardButton(text=f"Edit Case {c.id}", callback_data=f"lawyer_case_{c.id}")])

    kb.append([InlineKeyboardButton(text=_("btn_back"), callback_data="lawyer_back")])
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@router.callback_query(F.data.startswith("lawyer_case_"))
async def edit_case(callback: CallbackQuery, state: FSMContext, _, db_user: User, session: AsyncSession):
    case_id = int(callback.data.split("_")[2])

    case = await CaseService.get_case(session, case_id)

    # Action menu for case
    kb = [
        [InlineKeyboardButton(text=_("btn_change_status"), callback_data=f"lawyer_status_{case_id}")],
        [InlineKeyboardButton(text=_("btn_back"), callback_data="lawyer_cases")]
    ]

    # Log view
    stmt = select(Lawyer).where(Lawyer.user_id == db_user.id)
    lawyer = (await session.execute(stmt)).scalar_one()
    await CaseService.log_audit(session, lawyer.id, db_user.telegram_id, "VIEW_CASE", "case", case_id)

    await callback.message.edit_text(_("lawyer_case_edit", case_id=case_id), reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@router.callback_query(F.data.startswith("lawyer_status_"))
async def change_status_prompt(callback: CallbackQuery, state: FSMContext, _):
    case_id = int(callback.data.split("_")[2])
    await state.update_data(case_id=case_id)

    kb = []
    for st in CaseStatus:
        kb.append([InlineKeyboardButton(text=st.value, callback_data=f"lawyer_setst_{st.value}")])

    await callback.message.edit_text(_("lawyer_pick_status"), reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
    await state.set_state(LawyerStates.changing_status)

@router.callback_query(LawyerStates.changing_status, F.data.startswith("lawyer_setst_"))
async def set_status(callback: CallbackQuery, state: FSMContext, _, db_user: User, session: AsyncSession):
    status_str = callback.data.split("_")[2]
    data = await state.get_data()
    case_id = data["case_id"]

    case = await CaseService.change_status(session, case_id, CaseStatus(status_str), "Status updated by lawyer")

    stmt = select(Lawyer).where(Lawyer.user_id == db_user.id)
    lawyer = (await session.execute(stmt)).scalar_one()
    await CaseService.log_audit(session, lawyer.id, db_user.telegram_id, "CHANGE_STATUS", "case", case_id, f"To {status_str}")

    # Notify client
    stmt = select(User).join(Client).where(Client.id == case.client_id)
    client_user = (await session.execute(stmt)).scalar_one()

    try:
        from aiogram import Bot
        bot: Bot = callback.bot
        await bot.send_message(client_user.telegram_id, _("case_status_changed_notify", title=case.title, status=status_str))
    except Exception:
        pass

    await state.clear()
    await callback.message.edit_text(_("lawyer_status_updated"), reply_markup=lawyer_main_keyboard(_))

@router.callback_query(F.data == "lawyer_templates")
async def lawyer_templates(callback: CallbackQuery, _, db_user: User, session: AsyncSession):
    stmt = select(Lawyer).where(Lawyer.user_id == db_user.id)
    lawyer = (await session.execute(stmt)).scalar_one()

    stmt = select(DocumentTemplate).where(DocumentTemplate.lawyer_id == lawyer.id)
    templates = (await session.execute(stmt)).scalars().all()

    if not templates:
        text = _("lawyer_no_templates")
    else:
        text = _("lawyer_templates_list") + "\n"
        for t in templates:
            text += f"- {t.name}\n"

    await callback.message.edit_text(text, reply_markup=lawyer_main_keyboard(_))

@router.callback_query(F.data == "lawyer_back")
async def lawyer_back(callback: CallbackQuery, _):
    await callback.message.edit_text(_("lawyer_panel"), reply_markup=lawyer_main_keyboard(_))