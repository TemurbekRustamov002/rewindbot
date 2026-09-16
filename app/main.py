import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.redis import close_redis
from app.db.session import engine
import app.models  # Ensures all tables are registered on Base.metadata
from app.db.base import Base
from app.telegram.bot import bot, register_all_handlers
from app.telegram.webhook import webhook_router

setup_logging(level=settings.LOG_LEVEL, json_logs=(settings.ENVIRONMENT == "production"))
logger = logging.getLogger("rewind.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Starting {settings.PROJECT_NAME} in {settings.ENVIRONMENT} mode...")

    # 1. Initialize DB tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database schemas verified.")

    # 2. Register Telegram Handlers
    register_all_handlers()

    # 3. Setup Telegram Webhook (if not in local polling test)
    if settings.BOT_TOKEN != "DUMMY_TOKEN_REPLACE_ME" and "http" in settings.WEBHOOK_HOST:
        try:
            webhook_url = f"{settings.WEBHOOK_HOST.rstrip('/')}{settings.WEBHOOK_PATH}"
            await bot.set_webhook(
                url=webhook_url,
                secret_token=settings.WEBHOOK_SECRET,
                allowed_updates=[
                    "message",
                    "edited_message",
                    "business_connection",
                    "business_message",
                    "edited_business_message",
                    "deleted_business_messages",
                    "callback_query",
                    "pre_checkout_query",
                    "successful_payment"
                ],
                drop_pending_updates=False
            )
            logger.info(f"Telegram webhook configured: {webhook_url}")
        except Exception as e:
            logger.error(f"Failed to set Telegram webhook: {e}")

    yield

    # Shutdown
    logger.info("Shutting down Rewind Bot...")
    try:
        await bot.session.close()
    except Exception:
        pass
    await close_redis()
    await engine.dispose()
    logger.info("Shutdown complete.")


app = FastAPI(
    title="Rewind Bot API",
    version="1.0.0",
    lifespan=lifespan
)

# Include webhook router
app.include_router(webhook_router)


@app.get("/health")
async def health_check():
    """Health check endpoint for container probes and load balancers."""
    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT
    }


@app.get("/")
async def root():
    return {"message": "Rewind Bot API is running."}
