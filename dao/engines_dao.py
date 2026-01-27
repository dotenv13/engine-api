from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import Engine

class EngineDAO:
    async def list_engines(self,
                           session: AsyncSession,
                           make: Optional[str] = None,
                           model: Optional[str] = None,
                           year: Optional[str] = None,
                           limit: int = 20,
                           offset: int = 0,
                           ) -> List[Engine]:

        result = select(Engine).options(selectinload(Engine.images))

        if make:
            result = result.where(Engine.make == make)
        if model:
            result = result.where(Engine.model == model)
        if year:
            result = result.where(Engine.year == year)

        #пагинация
        result = result.limit(limit).offset(offset)

        engines = await session.execute(result)
        return engines.scalars().all()

    async def get_engine(self,
                         session: AsyncSession,
                         product_id: int
                         ) -> Engine:
        result = await session.execute(select(Engine).where(Engine.product_id == product_id).options(selectinload(Engine.images)))
        return result.scalars().one_or_none()

