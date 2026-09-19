from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from bot.database.models import DocumentTemplate, GeneratedDocument, Client, Lawyer
from docxtpl import DocxTemplate
import os
import time

class DocumentService:
    @staticmethod
    async def get_lawyer_templates(session: AsyncSession, lawyer_id: int) -> List[DocumentTemplate]:
        stmt = select(DocumentTemplate).where(DocumentTemplate.lawyer_id == lawyer_id)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_template(session: AsyncSession, template_id: int) -> DocumentTemplate | None:
        stmt = select(DocumentTemplate).where(DocumentTemplate.id == template_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def generate_document(
        session: AsyncSession,
        template: DocumentTemplate,
        client: Client,
        answers: Dict[str, Any],
        disclaimer: str
    ) -> GeneratedDocument:
        doc = DocxTemplate(template.file_path)

        # Add disclaimer to answers for doc generation if needed
        context = answers.copy()

        doc.render(context)

        os.makedirs("generated", exist_ok=True)
        filename = f"generated/doc_{client.id}_{int(time.time())}.docx"
        doc.save(filename)

        # Now we need to append the disclaimer text to the document or just rely on
        # disclaimer being in the context. If the template doesn't have a placeholder for disclaimer,
        # we can append it directly using docx.
        from docx import Document
        plain_doc = Document(filename)
        plain_doc.add_paragraph(disclaimer).italic = True
        plain_doc.save(filename)

        gen_doc = GeneratedDocument(
            template_id=template.id,
            client_id=client.id,
            file_path=filename
        )
        session.add(gen_doc)
        await session.flush()

        return gen_doc