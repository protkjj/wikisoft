"""
Telegram Bot 설정
"""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

DEFAULT_API_URL = "http://127.0.0.1:8004"
DEFAULT_API_TIMEOUT = 10.0


def _env_float(name: str, default: float) -> float:
    """숫자 환경변수 로드 (잘못된 값이면 기본값)."""
    try:
        return float(os.getenv(name, ""))
    except ValueError:
        return default


@dataclass
class Config:
    """봇 설정"""
    bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id: str = os.getenv("TELEGRAM_CHAT_ID", "")

    # WIKISOFT4 백엔드 연결
    api_base_url: str = os.getenv("WIKISOFT4_API_URL", DEFAULT_API_URL)
    api_key: str = os.getenv("WIKISOFT4_API_KEY", "")
    api_token: str = os.getenv("WIKISOFT4_API_TOKEN", "")
    api_timeout: float = _env_float("WIKISOFT4_API_TIMEOUT", DEFAULT_API_TIMEOUT)

    # 검증 관련
    allowed_users: list = None  # None이면 모든 사용자 허용

    def __post_init__(self):
        self.api_base_url = (self.api_base_url or DEFAULT_API_URL).rstrip("/")

    def is_notify_configured(self) -> bool:
        """알림 발송에 필요한 설정이 모두 있는지 확인."""
        return bool(self.bot_token and self.chat_id)

    def validate(self) -> None:
        """봇 기동 전 필수 설정 확인.

        알림 전용(Notifier)이나 API 클라이언트만 쓰는 경우에는 봇 토큰이 없어도
        임포트가 가능해야 하므로, 검증은 임포트 시점이 아니라 bot.main()에서 한다.
        """
        if not self.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN 환경변수가 필요합니다")


config = Config()
