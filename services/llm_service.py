# services/llm_service.py
import requests
import os
import json
from loguru import logger
from bot.config import config


class LLMClient:
    """
    Универсальный клиент для работы с LLM через OpenRouter.
    Можно использовать любые модели, указав их имя в payload.
    """

    def __init__(
        self,
        api_url: str = None,
        api_key: str = None,
        model_name: str = None
    ):
        self.api_url = api_url or "https://openrouter.ai/api/v1/chat/completions"
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.model_name = model_name or "tngtech/deepseek-r1t2-chimera:free"

        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY не найден. Установи переменную окружения.")

    def parse_message(self, message_text: str) -> dict:
        """
        Отправляет сообщение в выбранную LLM и возвращает структурированный результат.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            # Можно указать сайт или название проекта для OpenRouter-рейтинга
            "HTTP-Referer": "http://localhost",
            "X-Title": "Construction Parser Bot"
        }

        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Ты помощник инженера-строителя. "
                        "Извлеки из сообщения три поля: 'Вид работ', 'Объем', 'Комментарий'. "
                        "Если данных нет — оставь пустыми. "
                        "Ответ верни строго в формате JSON, например: "
                        "{\"Вид работ\": \"бетонирование перекрытия\", \"Объем\": \"25 м³\", \"Комментарий\": \"работы завершены\"}."
                    )
                },
                {"role": "user", "content": message_text}
            ],
            "temperature": 0.2
        }

        try:
            response = requests.post(self.api_url, headers=headers, data=json.dumps(payload))
            response.raise_for_status()
            content = response.json()

            # Попытка извлечь текст из ответа
            text = content["choices"][0]["message"]["content"].strip()
            logger.debug(f"LLM raw response: {text}")

            # Попытка интерпретировать как JSON
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                logger.warning("Ответ не является чистым JSON, пробуем извлечь вручную.")
                # Простейшая "чистка" JSON, если LLM вернула с комментарием
                json_str = text[text.find("{"): text.rfind("}") + 1]
                data = json.loads(json_str)

            logger.info(f"LLM parsed: {data}")
            return data

        except Exception as e:
            logger.error(f"Ошибка при обработке через LLM: {e}")
            return {"Вид работ": "", "Объем": "", "Комментарий": message_text}
