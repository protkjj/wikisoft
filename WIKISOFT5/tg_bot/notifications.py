"""
알림 발송 모듈

Excel에서 검증 완료 시 호출하여 Telegram으로 알림 발송
"""

import httpx
from datetime import datetime
from typing import Optional

from tg_bot.config import config


class Notifier:
    """텔레그램 알림 발송"""

    API_URL = "https://api.telegram.org/bot{token}/sendMessage"

    def __init__(self, bot_token: str = None, chat_id: str = None):
        self.bot_token = bot_token or config.bot_token
        self.chat_id = chat_id or config.chat_id

    def is_configured(self) -> bool:
        """발송에 필요한 토큰/채팅 ID가 있는지 확인."""
        return bool(self.bot_token and self.chat_id)

    async def send(self, text: str, parse_mode: str = "HTML") -> bool:
        """메시지 발송 (설정이 없으면 조용히 건너뜀)"""
        if not self.is_configured():
            print("알림 건너뜀: TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID 미설정")
            return False

        url = self.API_URL.format(token=self.bot_token)

        async with httpx.AsyncClient(timeout=10) as client:
            try:
                resp = await client.post(url, json={
                    "chat_id": self.chat_id,
                    "text": text,
                    "parse_mode": parse_mode,
                })
                return resp.status_code == 200
            except Exception as e:
                print(f"알림 발송 실패: {e}")
                return False

    async def send_validation_result(
        self,
        filename: str,
        status: str,  # "ok", "warning", "error"
        errors: int,
        warnings: int,
        row_count: int,
        details: Optional[str] = None,
    ) -> bool:
        """검증 결과 알림"""
        emoji = {"ok": "✅", "warning": "⚠️", "error": "❌"}.get(status, "📋")

        lines = [
            f"<b>{emoji} 검증 완료</b>",
            "",
            f"📁 <code>{filename}</code>",
            f"📊 오류 {errors}건 / 경고 {warnings}건",
            f"👥 {row_count}행",
            f"🕐 {datetime.now().strftime('%H:%M')}",
        ]

        if details:
            lines.append(f"\n💬 {details}")

        return await self.send("\n".join(lines))


# 간편 함수
async def notify_validation(
    filename: str,
    status: str,
    errors: int,
    warnings: int,
    row_count: int,
) -> bool:
    """검증 결과 알림 (간편 함수)"""
    notifier = Notifier()
    return await notifier.send_validation_result(
        filename=filename,
        status=status,
        errors=errors,
        warnings=warnings,
        row_count=row_count,
    )
