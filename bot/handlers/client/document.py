from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from bot.states.document import DocumentFillingState
from bot.database.models import Client, User
from bot.services.document import DocumentService
from bot.keyboards.client import templates_keyboard, cancel_keyboard
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import re

router = Router()

@router.message(Command("templates"))
async def list_templates(message: Message, state: FSMContext, _, db_user: User, session: AsyncSession):
    if not db_user or db_user.role.value != "client":
        return

    stmt = select(Client).where(Client.user_id == db_user.id)
    result = await session.execute(stmt)
    client = result.scalar_one_or_none()

    if not client:
        return await message.answer(_("no_lawyer_assigned"))

    templates = await DocumentService.get_lawyer_templates(session, client.lawyer_id)

    if not templates:
        return await message.answer(_("no_templates"))

    await message.answer(_("pick_template"), reply_markup=templates_keyboard(templates, _))
    await state.set_state(DocumentFillingState.picking_template)
    await state.update_data(client_id=client.id)

@router.callback_query(F.data == "cancel")
async def cancel_action(callback: CallbackQuery, state: FSMContext, _):
    await state.clear()
    await callback.message.edit_text(_("action_cancelled"))
    await callback.answer()

@router.callback_query(DocumentFillingState.picking_template, F.data.startswith("tpl_"))
async def pick_template(callback: CallbackQuery, state: FSMContext, _, session: AsyncSession):
    template_id = int(callback.data.split("_")[1])

    template = await DocumentService.get_template(session, template_id)
    if not template:
        return await callback.answer(_("template_not_found"), show_alert=True)

    await state.update_data(
        template_id=template.id,
        questions=template.questions,
        current_q_index=0,
        answers={}
    )

    q = template.questions[0]
    await callback.message.edit_text(q["question"], reply_markup=cancel_keyboard(_))
    await state.set_state(DocumentFillingState.answering_questions)
    await callback.answer()

@router.message(DocumentFillingState.answering_questions)
async def answer_question(message: Message, state: FSMContext, _, session: AsyncSession):
    data = await state.get_data()
    q_index = data["current_q_index"]
    questions = data["questions"]
    answers = data["answers"]

    current_q = questions[q_index]

    # Validation
    if "validation" in current_q and current_q["validation"]:
        pattern = current_q["validation"]
        if not re.match(pattern, message.text):
            return await message.answer(_("invalid_format") + "\n" + current_q["question"], reply_markup=cancel_keyboard(_))

    answers[current_q["key"]] = message.text

    if q_index + 1 < len(questions):
        # Next question
        await state.update_data(current_q_index=q_index + 1, answers=answers)
        next_q = questions[q_index + 1]
        await message.answer(next_q["question"], reply_markup=cancel_keyboard(_))
    else:
        # Generate document
        await message.answer(_("generating_document"))

        template = await DocumentService.get_template(session, data["template_id"])
        stmt = select(Client).where(Client.id == data["client_id"])
        client = (await session.execute(stmt)).scalar_one()

        disclaimer = _("disclaimer")
        gen_doc = await DocumentService.generate_document(session, template, client, answers, disclaimer)

        # Send file to client
        doc_file = FSInputFile(gen_doc.file_path)
        await message.answer_document(doc_file, caption=disclaimer)

        # Notify lawyer (simplified notification)
        stmt = select(User).where(User.id == template.lawyer.user_id)
        lawyer_user = (await session.execute(stmt)).scalar_one()

        try:
            from aiogram import Bot
            bot: Bot = message.bot
            await bot.send_message(lawyer_user.telegram_id, _("doc_generated_notify", client_id=client.id))
        except Exception:
            pass

        await state.clear()