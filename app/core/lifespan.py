from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Iniciando JARVIS-OS...")

    yield

    logger.info("🛑 Cerrando JARVIS-OS...")
