# Telegram Build Bot — initial implementation

This repository contains an MVP Telegram bot for collecting free-text construction progress reports from foremen and writing them to Google Sheets.

## Quick start
1. Copy `.env.example` to `.env` and fill values.
2. Place your Google service account JSON at the path specified in `.env`.
3. Provide a `whitelist.json` file with structure: `{"ids": [123456789], "usernames": ["proраб"]}`
4. Build and run:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python bot/main.py
```

## Docker
Build image:
```
docker build -t telegram-build-bot:latest .
```
Run container (mount secrets):
```
docker run -v /path/to/google.json:/secrets/google-service-account.json -v /path/to/whitelist.json:/data/whitelist.json telegram-build-bot:latest
```

# Notes
- This is an MVP. Webhook mode, advanced admin commands, and robust monitoring are planned in next iterations.
