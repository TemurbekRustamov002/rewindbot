import logging
from fastapi import APIRouter, Request, Header, HTTPException, status
from aiogram.types import Update
from app.core.config import settings
from app.core.redis import is_update_processed
from app.telegram.bot import bot, dp

logger = logging.getLogger(__name__)
webhook_router = APIRouter()


@webhook_router.post(settings.WEBHOOK_PATH)
async def handle_telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str = Header(None)
):
    """
    FastAPI Webhook endpoint for Telegram updates.
    Validates secret token, applies deduplication, and feeds update to aiogram dispatcher.
    """
    # 1. Validate Secret Token
    if settings.WEBHOOK_SECRET and x_telegram_bot_api_secret_token != settings.WEBHOOK_SECRET:
        logger.warning("Rejected webhook update: Invalid secret token.")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid token")

    # 2. Parse JSON payload
    try:
        raw_json = await request.json()
        update = Update.model_validate(raw_json, context={"bot": bot})
    except Exception as e:
        logger.error(f"Error deserializing Telegram update: {e}")
        return {"ok": True}

    # 3. Idempotency Check (Deduplication)
    if await is_update_processed(update.update_id):
        logger.info(f"Duplicate update {update.update_id} skipped.")
        return {"ok": True}

    # 4. Dispatch update
    try:
        await dp.feed_update(bot, update)
    except Exception as e:
        logger.error(f"Error processing update {update.update_id}: {e}", exc_info=True)

    return {"ok": True}
