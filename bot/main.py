import asyncio
import logging
import os
from loguru import logger
from datetime import datetime
import pytz
import json
import sys


from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardRemove

from .config import config
from .auth import Auth
from .google_sheets import GoogleSheetsClient
from .persistent_queue import PersistentQueue

# Configure logger
logger.remove()
logger.add(sys.stderr, level=config.log_level)

# -----------------------------
# Ensure data dir inside project
# -----------------------------
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
os.makedirs(DATA_DIR, exist_ok=True)

# Path to SQLite queue DB
QUEUE_DB_PATH = os.path.join(DATA_DIR, "queue.db")

auth = Auth()
queue = PersistentQueue(db_path=QUEUE_DB_PATH)

# Initialize Telegram bot
if not config.telegram_token:
    logger.error('TELEGRAM_BOT_TOKEN is not set. Exiting.')
    raise SystemExit(1)

bot = Bot(token=config.telegram_token)
dp = Dispatcher()

# Helper: format timestamps
def now_timestamps():
    utc = datetime.utcnow().replace(tzinfo=pytz.utc)
    local = utc.astimezone(pytz.timezone(config.timezone))
    return utc.isoformat(), local.isoformat()

async def try_flush_queue(gsheet_client: GoogleSheetsClient):
    # Try to drain queue
    while True:
        item = queue.pop()
        if not item:
            break
        id_ = item['id']
        payload = item['payload']
        try:
            gsheet_client.append_row(payload)
            queue.mark_done(id_)
            logger.info(f'Flushed queued item {id_}')
        except Exception as e:
            logger.exception('Failed to flush queued item')
            queue.mark_failed(id_)
            break

@dp.message()
async def handle_message(message: types.Message):
    # Only accept text messages
    user = message.from_user
    username = user.username or ''
    user_id = user.id

    if not auth.is_allowed(user_id, username):
        await message.answer('Вы не зарегистрированы для отправки данных. Обратитесь к ответственному за проект.')
        logger.info(f'Unauthorized message from {user_id} / {username}')
        return

    if not message.text:
        await message.answer('Отправляйте, пожалуйста, только текстовые сообщения по ходу работ.')
        return

    ts_utc, ts_local = now_timestamps()

    payload = {
        'timestamp_utc': ts_utc,
        'timestamp_local': ts_local,
        'telegram_user_id': user_id,
        'telegram_username': username,
        'chat_id': message.chat.id,
        'message_id': message.message_id,
        'message_text': message.text,
        'record_status': 'queued',
        'note': ''
    }

    # Try to append directly; on failure push to queue
    try:
        gs = GoogleSheetsClient(config.google_credentials, config.spreadsheet_id)
        gs.append_row(payload)
        await message.answer('Сообщение принято — спасибо.')
        logger.info(f'Recorded message from {user_id} / {username}')
        # attempt to flush queued items too
        await try_flush_queue(gs)
    except Exception as e:
        logger.exception('Failed to write to Google Sheets, saving to queue')
        queue.push(payload)
        await message.answer('Сервер временно недоступен — сообщение сохранено и будет отправлено позже.')

@dp.message(Command('whoami'))
async def cmd_whoami(message: types.Message):
    user = message.from_user
    await message.answer(f'Ваш Telegram ID: {user.id}\nUsername: @{user.username}' if user.username else f'Ваш Telegram ID: {user.id}\n(Username отсутствует)')

@dp.message(Command('status'))
async def cmd_status(message: types.Message):
    if message.from_user.id not in config.admin_ids:
        await message.answer('Команда доступна только администраторам.')
        return
    # Basic status info
    # show queue length
    import sqlite3
    conn = sqlite3.connect(QUEUE_DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM queue WHERE status IN ("queued","processing")')
    count = cur.fetchone()[0]
    conn.close()
    await message.answer(f'Bot status: OK\nQueued items: {count}')

async def main():
    if config.mode == 'polling':
        await dp.start_polling(bot)
    else:
        # webhook mode not implemented in MVP; fallback to polling
        await dp.start_polling(bot)

if __name__ == '__main__':
    import sys
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info('Shutting down...')