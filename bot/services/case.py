from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from bot.database.models import Case, CaseStatusHistory, AuditLog, CaseStatus, Client, Lawyer
from typing import List

class CaseService:
    @staticmethod
    async def create_case(session: AsyncSession, title: str, client_id: int, lawyer_id: int) -> Case:
        case = Case(
            title=title,
            client_id=client_id,
            lawyer_id=lawyer_id,
            status=CaseStatus.new
        )
        session.add(case)
        await session.flush()

        history = CaseStatusHistory(
            case_id=case.id,
            status=CaseStatus.new,
            note="Case created"
        )
        session.add(history)
        await session.flush()

        return case

    @staticmethod
    async def change_status(session: AsyncSession, case_id: int, status: CaseStatus, note: str = None) -> Case:
        stmt = select(Case).where(Case.id == case_id)
        case = (await session.execute(stmt)).scalar_one()

        case.status = status

        history = CaseStatusHistory(
            case_id=case.id,
            status=status,
            note=note
        )
        session.add(history)
        await session.flush()

        return case

    @staticmethod
    async def log_audit(session: AsyncSession, lawyer_id: int, telegram_id: int, action: str, target_type: str, target_id: int, details: str = None):
        log = AuditLog(
            lawyer_id=lawyer_id,
            actor_telegram_id=telegram_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            details=details
        )
        session.add(log)
        await session.flush()

    @staticmethod
    async def get_lawyer_cases(session: AsyncSession, lawyer_id: int) -> List[Case]:
        stmt = select(Case).where(Case.lawyer_id == lawyer_id)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_client_cases(session: AsyncSession, client_id: int) -> List[Case]:
        stmt = select(Case).where(Case.client_id == client_id)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_case(session: AsyncSession, case_id: int) -> Case | None:
        stmt = select(Case).where(Case.id == case_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()