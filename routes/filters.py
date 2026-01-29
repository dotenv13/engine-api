from fastapi import APIRouter, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from db.database import get_session
from services.filters_service import filters_service

router = APIRouter(prefix="/filters", tags=["Filters"])

@router.get('/makes', response_model = List[str])
async def get_makes(session: AsyncSession = Depends(get_session)
                    ):
    return await filters_service.get_makes(session)

@router.get('/models', response_model = List[str])
async def get_models(session: AsyncSession = Depends(get_session),
                     make: Optional[str] = Query(None)
                     ):
    return await filters_service.get_models(session, make)

@router.get('/years', response_model = List[str])
async def get_years(session: AsyncSession = Depends(get_session),
                    make : Optional[str] = Query(None),
                    model: Optional[str] = Query(None)
                    ):
    return await filters_service.get_years(session, make, model)



