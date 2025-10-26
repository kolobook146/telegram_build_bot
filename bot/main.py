import asyncio
import os
import sys
from loguru import logger
from aiogram import Bot, Dispatcher
from bot.config import config
from services.auth import Auth
from services.google_sheets import GoogleSheetsClient
from bot.persistent_queue import PersistentQueue
from bot.handlers import register_handlers

# -----------------------------
# Конфигурация логгера
# -----------------------------
logger.remove()
logger.add(sys.stderr, level=config.log_level)

# -----------------------------
# Подготовка путей и окружения
# -----------------------------
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
os.makedirs(DATA_DIR, exist_ok=True)
QUEUE_DB_PATH = os.path.join(DATA_DIR, "queue.db")

# -----------------------------
# Инициализация зависимостей
# -----------------------------
auth = Auth()
queue = PersistentQueue(db_path=QUEUE_DB_PATH)
gsheets = GoogleSheetsClient(config.google_credentials, config.spreadsheet_id)

# -----------------------------
# Инициализация Telegram бота
# -----------------------------
if not config.telegram_token:
    logger.error("TELEGRAM_BOT_TOKEN is not set. Exiting.")
    raise SystemExit(1)

bot = Bot(token=config.telegram_token)
dp = Dispatcher()

# -----------------------------
# Регистрация обработчиков
# -----------------------------
register_handlers(dp, auth, queue, gsheets)

# -----------------------------
# Точка входа
# -----------------------------
async def main():
    if config.mode == "polling":
        await dp.start_polling(bot)
    else:
        await dp.start_polling(bot)  # webhook не реализован

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down...")
