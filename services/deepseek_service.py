# services/deepseek_service.py
import requests
import os
from loguru import logger
import json
from bot.config import config

class DeepSeekClient:
    def __init__(self, api_url: str = None, api_key: str = None):
        self.api_url = api_url or config.deepseek_api_url
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")

    def parse_message(self, message_text: str) -> dict:
        """
        Отправляет сообщение в DeepSeek и возвращает структурированный результат.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Ты помощник инженера-строителя. "
                        "Твоя задача — выделить из сообщения следующие поля: "
                        "'Вид работ', 'Объем', 'Комментарий'. Если данных нет — оставь поле пустым. "
                        "Ответ верни строго в формате JSON."
                    )
                },
                {"role": "user", "content": message_text}
            ],
            "temperature": 0.2
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=payload)
            response.raise_for_status()
            content = response.json()
            text = content["choices"][0]["message"]["content"]
            data = json.loads(text)
            logger.info(f"DeepSeek parsed: {data}")
            return data
        except Exception as e:
            logger.error(f"Ошибка при обработке через DeepSeek: {e}")
            return {"Вид работ": "", "Объем": "", "Комментарий": message_text}
