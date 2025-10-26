from dataclasses import dataclass, field
import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    telegram_token: str = os.getenv('TELEGRAM_BOT_TOKEN')
    google_credentials: str = os.getenv('GOOGLE_CREDENTIALS_JSON')
    spreadsheet_id: str = os.getenv('SPREADSHEET_ID')
    whitelist_json: str = os.getenv('WHITELIST_JSON', './whitelist.json')
    mode: str = os.getenv('BOT_MODE', 'polling')
    admin_ids: list[int] = field(default_factory=lambda: [int(x) for x in os.getenv('ADMIN_IDS', '').split(',') if x.strip()])
    timezone: str = os.getenv('TIMEZONE', 'UTC')
    log_level: str = os.getenv('LOG_LEVEL', 'INFO')

    # --- DeepSeek configuration ---
    deepseek_api_url: str = os.getenv('DEEPSEEK_API_URL', 'https://api.deepseek.com/v1/chat/completions')
    deepseek_api_key: str = os.getenv('DEEPSEEK_API_KEY', '')

config = Config()