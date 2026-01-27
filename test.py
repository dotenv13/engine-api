from sqlalchemy.orm import session
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from db.models import Engine


from dao.engines_dao import EngineDAO
dao = EngineDAO()

total, items = await dao.list_engines(session, make="Volvo", limit=5, offset=0)
print(total, len(items))
print(items[0].product_id, len(items[0].images))
