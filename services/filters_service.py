from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from dao.filters_dao import filters_dao


class FiltersService:
    async def get_makes(self,
                        session: AsyncSession,
                        ) -> List[str]:
        return await filters_dao.get_makes(session)

    async def get_models(self,
                         session: AsyncSession,
                         make: Optional[str] = None
                         ) -> List[str]:
        return await filters_dao.get_models(session, make)

    async def get_years(self,
                        session: AsyncSession,
                        make: Optional[str] = None,
                        model: Optional[str] = None
                        ) -> List[str]:
        return await filters_dao.get_years(session, make, model)

filters_service = FiltersService()
