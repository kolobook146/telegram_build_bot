from datetime import datetime
import pytz
import sqlite3
from aiogram import types
from aiogram import F
from aiogram.filters import Command
from loguru import logger

from bot.config import config
from services.llm_service import LLMClient


# -----------------------------
# Вспомогательные функции
# -----------------------------
def now_timestamps(timezone: str | None = None) -> tuple[str, str]:
    tz = timezone or config.timezone
    utc_dt = datetime.utcnow().replace(tzinfo=pytz.utc)
    local_dt = utc_dt.astimezone(pytz.timezone(tz))
    return utc_dt.isoformat(), local_dt.isoformat()


async def try_flush_queue(queue, gsheet_client):
    while True:
        item = queue.pop()
        if not item:
            break
        id_ = item["id"]
        payload = item["payload"]
        try:
            gsheet_client.append_row(payload)
            queue.mark_done(id_)
            logger.info(f"Flushed queued item {id_}")
        except Exception:
            logger.exception("Failed to flush queued item")
            queue.mark_failed(id_)
            break


# -----------------------------
# Основная регистрация хендлеров
# -----------------------------
def register_handlers(dp, auth, queue, gsheet_client):
    llm_client = LLMClient()

    @dp.message(F.text & ~F.text.startswith("/"))
    async def handle_message(message: types.Message):
        user = message.from_user
        username = user.username or ""
        user_id = user.id

        # Проверяем, авторизован ли пользователь
        if not auth.is_allowed(user_id, username):
            await message.answer("Вы не зарегистрированы для отправки данных. Обратитесь к ответственному за проект.")
            logger.info(f"Unauthorized message from {user_id} / {username}")
            return

        # Игнорируем не-текстовые сообщения
        if not message.text:
            await message.answer("Отправляйте, пожалуйста, только текстовые сообщения по ходу работ.")
            return

        ts_utc, ts_local = now_timestamps(config.timezone)

        # -----------------------------
        # Обработка через llm_client
        # -----------------------------
        try:
            parsed = llm_client.parse_message(message.text)
            logger.info(f"llm_client parsed: {parsed}")
        except Exception as e:
            logger.exception("llm_client parsing failed")
            parsed = {"Вид работ": "", "Объем": "", "Комментарий": message.text}

        # -----------------------------
        # Формируем запись
        # -----------------------------
        payload = {
            "timestamp_utc": ts_utc,
            "timestamp_local": ts_local,
            "telegram_user_id": user_id,
            "telegram_username": username,
            "message_text": message.text,
            "record_status": "queued",
            "work_type": parsed.get("Вид работ", ""),
            "volume": parsed.get("Объем", ""),
            "comment": parsed.get("Комментарий", ""),
        }

        # -----------------------------
        # Пытаемся записать в Google Sheets
        # -----------------------------
        try:
            gsheet_client.append_row(payload)
            await message.answer("Сообщение принято — данные успешно зафиксированы ✅")
            logger.info(f"Recorded message from {user_id} / {username}")
            await try_flush_queue(queue, gsheet_client)
        except Exception:
            logger.exception("Failed to write to Google Sheets, saving to queue")
            queue.push(payload)
            await message.answer("Сервер временно недоступен — сообщение сохранено и будет отправлено позже 🕓")

    # -----------------------------
    # Команда /whoami
    # -----------------------------
    @dp.message(Command("whoami"))
    async def cmd_whoami(message: types.Message):
        user = message.from_user
        await message.answer(
            f"Ваш Telegram ID: {user.id}\nUsername: @{user.username}"
            if user.username
            else f"Ваш Telegram ID: {user.id}\n(Username отсутствует)"
        )

    # -----------------------------
    # Команда /status
    # -----------------------------
    @dp.message(Command("status"))
    async def cmd_status(message: types.Message):
        if message.from_user.id not in auth.ids and message.from_user.username not in auth.usernames:
            await message.answer("Команда доступна только администраторам.")
            return

        conn = sqlite3.connect(queue.db_path)
        cur = conn.cursor()
        cur.execute('SELECT COUNT(*) FROM queue WHERE status IN ("queued","processing")')
        count = cur.fetchone()[0]
        conn.close()

        await message.answer(f"Bot status: OK\nQueued items: {count}")
