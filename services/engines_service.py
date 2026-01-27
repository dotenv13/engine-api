from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from dao.engines_dao import engine_dao   #мпортируем наш dao
from schemas.engine import EngineOut


class EnginesService:
    def _images_to_urls(self, engine) -> List[str]:
        """
        engine.images -> ["url1", "url2", ...]
        + сортировка по sort_order (чтобы порядок был стабильным)
        """
        if not getattr(engine, "images", None):
            return []

        # sort_order есть в БД, поэтому сортируем.
        images_sorted = sorted(engine.images, key=lambda img: img.sort_order)
        return [img.image_url for img in images_sorted]

    async def list_engines(self,
                           session: AsyncSession,
                           make: Optional[str] = None,
                           model: Optional[str] = None,
                           year: Optional[str] = None,
                           limit: int = 20,
                           offset: int = 0,
                           ) -> List[EngineOut]:
        engines = await engine_dao.list_engines(
            session=session,
            make=make,
            model=model,
            year=year,
            limit=limit,
            offset=offset,
        )

        # превращаем ORM -> EngineOut и добавляем images как urls
        return [
            EngineOut(
                product_id=e.product_id,
                title=e.title,
                make=e.make,
                model=e.model,
                year=e.year,
                engine_code=e.engine_code,
                engine_type=e.engine_type,
                price=e.price,
                currency=e.currency,
                stock_text=e.stock_text,
                oem=e.oem,
                description=e.description,
                images=self._images_to_urls(e),
            )
            for e in engines
        ]

    async def get_engine(
        self,
        session: AsyncSession,
        product_id: int,
    ) -> Optional[EngineOut]:
        engine = await engine_dao.get_engine(session=session, product_id=product_id)
        if not engine:
            return None

        return EngineOut(
            product_id=engine.product_id,
            title=engine.title,
            make=engine.make,
            model=engine.model,
            year=engine.year,
            engine_code=engine.engine_code,
            engine_type=engine.engine_type,
            price=engine.price,
            currency=engine.currency,
            stock_text=engine.stock_text,
            oem=engine.oem,
            description=engine.description,
            images=self._images_to_urls(engine),
        )


engines_service = EnginesService()