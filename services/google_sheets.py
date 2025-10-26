import gspread
from google.oauth2.service_account import Credentials
from typing import Dict, Any
from bot.config import config

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

class GoogleSheetsClient:
    def __init__(self, credentials_path: str, spreadsheet_id: str):
        self.spreadsheet_id = spreadsheet_id
        creds = Credentials.from_service_account_file(credentials_path, scopes=SCOPES)
        self.client = gspread.authorize(creds)
        self.sheet = self.client.open_by_key(spreadsheet_id).sheet1

    def append_row(self, row: Dict[str, Any]):
        """
        Добавляет строку в Google Sheets с расширенной структурой.
        Ожидаемые поля:
        timestamp_local, telegram_user_id, telegram_username,
        chat_id, message_id, message_text, work_type, volume, comment, record_status
        """
        values = [
            row.get('timestamp_local', ''),
            str(row.get('telegram_user_id', '')),
            row.get('telegram_username', ''),
            str(row.get('chat_id', '')),
            str(row.get('message_id', '')),
            row.get('message_text', ''),
            row.get('work_type', ''),       # Заполняется DeepSeek
            row.get('volume', ''),          # Заполняется DeepSeek
            row.get('comment', ''),         # Заполняется DeepSeek
            row.get('record_status', 'ok'),
        ]
        self.sheet.append_row(values, value_input_option='RAW')
