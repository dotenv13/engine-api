from typing import Optional, List
from sqlalchemy import select, distinct
from sqlalchemy.ext.asyncio import AsyncSession
from db.models import Engine

class FiltersDAO:
    async def get_makes(self,
                          session: AsyncSession,
                          ) -> List[str]:
        result = (
            select(distinct(Engine.make))
            .where(Engine.make.isnot(None))
            .order_by(Engine.make)
        )

        final = await session.execute(result)
        return [i[0] for i in final.all() if i[0]]

    async def get_models(self,
                           session: AsyncSession,
                           make: Optional[str] = None
                           ) -> List[str]:
        result = (
            select(distinct(Engine.model))
            .where(Engine.model.isnot(None))
        )
        if make:
            result = result.where(Engine.make == make)

        result = result.order_by(Engine.model)

        final = await session.execute(result)
        return [i[0] for i in final.all() if i[0]]

    async def get_years(self,
                          session: AsyncSession,
                          make: Optional[str] = None,
                          model: Optional[str] = None
                          ) -> List[str]:
        result = (
            select(distinct(Engine.year))
            .where(Engine.year.isnot(None))
        )
        if make:
            result = result.where(Engine.make == make)
        if model:
            result = result.where(Engine.model == model)

        result = result.order_by(Engine.year)

        final = await session.execute(result)
        return [i[0] for i in final.all() if i[0]]

filters_dao = FiltersDAO()
