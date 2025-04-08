from fastapi import FastAPI
import logging
from fastapi.middleware.cors import CORSMiddleware
from app.routers import router
from app.config import db_config
from contextlib import asynccontextmanager

logging.basicConfig(level=logging.INFO)  

@asynccontextmanager
async def lifespan(app):
    await db_config.start_db()
    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
