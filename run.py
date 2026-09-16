"""Rewind Bot - Universal Application Entrypoint & CLI.

Supports running API server, Polling mode, Background Workers, Schedulers,
and Database Management tasks.
"""

import argparse
import asyncio
import logging
import sys
from alembic import command as alembic_command
from alembic.config import Config as AlembicConfig
import uvicorn
from sqlalchemy import func, select

from app.core.config import settings
from app.core.logging import setup_logging
from app.db.base import Base
from app.db.session import async_session_factory, engine
import app.models  # Ensures all models are registered on Base.metadata
from app.telegram.bot import bot, dp, register_all_handlers

setup_logging(level=settings.LOG_LEVEL, json_logs=(settings.ENVIRONMENT == "production"))
logger = logging.getLogger("rewind.runner")


async def run_polling():
    """Runs bot locally using long-polling for development."""
    logger.info("Starting local development polling mode...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    register_all_handlers()

    # Drop any existing webhook before polling
    await bot.delete_webhook(drop_pending_updates=True)

    try:
        await dp.start_polling(
            bot,
            allowed_updates=[
                "message",
                "edited_message",
                "business_connection",
                "business_message",
                "edited_business_message",
                "deleted_business_messages",
                "callback_query",
                "pre_checkout_query",
                "successful_payment",
            ],
        )
    finally:
        await bot.session.close()


async def init_db_schema():
    """Initializes all database tables from SQLAlchemy models."""
    logger.info("Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("All database tables created successfully!")


def run_alembic_migrations():
    """Executes Alembic migrations to upgrade to latest revision."""
    logger.info("Executing Alembic migrations (upgrade head)...")
    alembic_cfg = AlembicConfig("alembic.ini")
    alembic_command.upgrade(alembic_cfg, "head")
    logger.info("Alembic migrations completed successfully.")


async def inspect_db_state():
    """Inspects database records and prints statistics summary."""
    from app.models.business_connection import BusinessConnection
    from app.models.chat import Chat
    from app.models.media import MediaObject
    from app.models.message import Message, MessageVersion
    from app.models.subscription import Payment, Subscription
    from app.models.user import User

    async with async_session_factory() as session:
        user_count = (await session.execute(select(func.count(User.id)))).scalar() or 0
        conn_count = (
            await session.execute(select(func.count(BusinessConnection.id)))
        ).scalar() or 0
        chat_count = (await session.execute(select(func.count(Chat.id)))).scalar() or 0
        msg_count = (await session.execute(select(func.count(Message.id)))).scalar() or 0
        deleted_count = (
            await session.execute(
                select(func.count(Message.id)).where(Message.is_deleted == True)  # noqa: E712
            )
        ).scalar() or 0
        versions_count = (
            await session.execute(select(func.count(MessageVersion.id)))
        ).scalar() or 0
        media_count = (await session.execute(select(func.count(MediaObject.id)))).scalar() or 0
        sub_count = (await session.execute(select(func.count(Subscription.id)))).scalar() or 0
        pay_count = (await session.execute(select(func.count(Payment.id)))).scalar() or 0

        print("\n================= DATABASE INSPECTION =================")
        print(f" Database URL:      {settings.DATABASE_URL}")
        print(f" Environment:       {settings.ENVIRONMENT}")
        print(" -----------------------------------------------------")
        print(f" Users:             {user_count}")
        print(f" Connections:       {conn_count}")
        print(f" Tracked Chats:     {chat_count}")
        print(f" Messages (Total):  {msg_count}")
        print(f" Deleted Messages:  {deleted_count}")
        print(f" Edited Versions:   {versions_count}")
        print(f" Media Objects:     {media_count}")
        print(f" Subscriptions:     {sub_count}")
        print(f" Payments (Stars):  {pay_count}")
        print("=======================================================\n")


def main():
    parser = argparse.ArgumentParser(
        prog="rewind",
        description="Rewind Bot - Telegram Chat Automation & Archive System CLI",
    )
    parser.add_argument(
        "--mode",
        choices=[
            "api",
            "polling",
            "worker",
            "scheduler",
            "init-db",
            "migrate",
            "inspect-db",
        ],
        default="api",
        help="Execution mode (default: api)",
    )
    parser.add_argument("--host", default="0.0.0.0", help="Host address for FastAPI server")
    parser.add_argument("--port", type=int, default=8000, help="Port for FastAPI server")

    args = parser.parse_args()

    if args.mode == "api":
        uvicorn.run("app.main:app", host=args.host, port=args.port, reload=settings.DEBUG)
    elif args.mode == "polling":
        asyncio.run(run_polling())
    elif args.mode == "worker":
        from app.workers.media_worker import run_media_worker

        asyncio.run(run_media_worker())
    elif args.mode == "scheduler":
        from app.workers.scheduler import run_scheduler

        asyncio.run(run_scheduler())
    elif args.mode == "init-db":
        asyncio.run(init_db_schema())
    elif args.mode == "migrate":
        run_alembic_migrations()
    elif args.mode == "inspect-db":
        asyncio.run(inspect_db_state())
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
