"""Telegram configuration — 환경변수에서 로드."""
import os

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")


def is_configured() -> bool:
    """텔레그램 설정이 완료되었는지 확인."""
    return bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)
