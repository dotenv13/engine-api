from fastapi import FastAPI, Request
from db.database import engine, Base
from routes import engines

app = FastAPI(title="Engines API with SQLAlchemy")

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

app.include_router(engines.router, tags=["engines"])