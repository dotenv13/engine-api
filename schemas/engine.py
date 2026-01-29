from typing import Optional, List
from pydantic import BaseModel


class EngineBase(BaseModel):
    product_id: int
    title: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[str] = None
    engine_code: Optional[str] = None
    engine_type: Optional[str] = None
    price: Optional[int] = None
    currency: Optional[str] = None
    stock_text: Optional[str] = None
    oem: Optional[str] = None
    description: Optional[str] = None

class EngineOut(EngineBase):
    images: List[str] = []

    # позволяет pydantic понимать ORM-объекты
    model_config = {"from_attributes": True}
