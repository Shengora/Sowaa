from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import TypeVar, Generic, Type, Any, Optional

from bot.database.core import Base

ModelType = TypeVar("ModelType", bound=Base)

class LawyerScopedRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get_by_id(self, session: AsyncSession, lawyer_id: int, obj_id: int) -> Optional[ModelType]:
        stmt = select(self.model).where(self.model.id == obj_id, self.model.lawyer_id == lawyer_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self, session: AsyncSession, lawyer_id: int) -> list[ModelType]:
        stmt = select(self.model).where(self.model.lawyer_id == lawyer_id)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, session: AsyncSession, obj_in: Any) -> ModelType:
        db_obj = self.model(**obj_in)
        session.add(db_obj)
        await session.flush()
        await session.refresh(db_obj)
        return db_obj