import json
import os
from typing import Set

from bot.config import config

class Auth:
    def __init__(self, whitelist_path: str = None):
        self.whitelist_path = whitelist_path or config.whitelist_json
        self._load()

    def _load(self):
        try:
            with open(self.whitelist_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # Expect list of telegram user ids or usernames
            self.ids = set(int(x) for x in data.get('ids', []) if str(x).isdigit())
            self.usernames = set(x.lower() for x in data.get('usernames', []))
        except Exception:
            self.ids = set()
            self.usernames = set()

    def is_allowed(self, user_id: int, username: str) -> bool:
        if user_id in self.ids:
            return True
        if username and username.lower() in self.usernames:
            return True
        return False