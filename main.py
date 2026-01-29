from fastapi import FastAPI
from db.database import engine, Base
from routes import engines, filters

app = FastAPI(title="Engines API with SQLAlchemy")

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

app.include_router(engines.router)
app.include_router(filters.router)