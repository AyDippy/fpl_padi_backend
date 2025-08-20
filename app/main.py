from fastapi import FastAPI
from app.db.session import Base, engine
from fastapi.middleware.cors import CORSMiddleware
from app.core.logging import logger
from app.models.user import User
from app.models.chat import ChatMessage
from app.api.v1 import api_routers


async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")

app = FastAPI(title="FPL Padi Backend", version="1.0.0")

app.include_router(prefix="/api/v1", router=api_routers)

@app.on_event("startup")
async def on_startup():
    await create_db_and_tables()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for CORS
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def read_root():
    """
    Root endpoint for the FPL Padi Backend.
    
    Returns a welcome message.
    """
    return {"message": "Welcome to FPL Padi"}


