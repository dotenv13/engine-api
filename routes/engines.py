from typing import Optional, List

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_session
from schemas.engine import EngineOut
from services.engines_service import engines_service

router = APIRouter(prefix="/engines", tags=["Engines"])


@router.get("/", response_model=List[EngineOut])
async def list_engines(session: AsyncSession = Depends(get_session),
                       make: Optional[str] = Query(None),
                       model: Optional[str] = Query(None),
                       year: Optional[str] = Query(None),
                       price_min: Optional[int] = Query(None, ge=0),
                       price_max: Optional[int] = Query(None, ge=0),
                       limit: int = Query(20, ge=1, le=200),
                       offset: int = Query(0, ge=0),
                       ):
    return await engines_service.list_engines(
        session=session,
        make=make,
        model=model,
        year=year,
        price_min=price_min,
        price_max=price_max,
        limit=limit,
        offset=offset,
    )

@router.get("/{product_id}", response_model=EngineOut)
async def get_engine(product_id: int,
                     session: AsyncSession = Depends(get_session),
                     ):
    engine = await engines_service.get_engine(session=session, product_id=product_id)
    if not engine:
        raise HTTPException(status_code=404, detail="Engine not found")
    return engine
