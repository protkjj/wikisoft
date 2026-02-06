"""
Telegram Notifier — 검증 결과 알림 발송

Graceful Degradation:
- 토큰 없으면 알림 건너뜀 (로그만 출력)
- 네트워크 실패해도 검증 결과는 정상 반환
"""

import httpx
from datetime import datetime
from typing import Optional

from .config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, is_configured

TELEGRAM_API = "https://api.telegram.org"


def _grade_from_confidence(score: float) -> str:
    """신뢰도 점수 → 등급 변환."""
    if score >= 0.95:
        return "S"
    elif score >= 0.90:
        return "A"
    elif score >= 0.85:
        return "B"
    elif score >= 0.80:
        return "C"
    else:
        return "D"


def _build_message(
    filename: str,
    error_count: int,
    warning_count: int,
    row_count: int,
    confidence: float,
    status: str,
) -> str:
    """알림 메시지 생성."""
    # 상태: 오류 0건 → 성공, 오류 있음 → 실패 (경고는 무관)
    if error_count == 0:
        status_emoji = "✅"
        status_text = "검증 성공"
    else:
        status_emoji = "❌"
        status_text = "검증 실패"

    grade = _grade_from_confidence(confidence)
    now = datetime.now().strftime("%H:%M")
    confidence_pct = f"{confidence * 100:.0f}%"

    return (
        f"{status_emoji} {status_text}\n"
        f"\n"
        f"📁 {filename}\n"
        f"📊 오류 {error_count}건 / 경고 {warning_count}건\n"
        f"👥 {row_count}행\n"
        f"🕐 {now}\n"
        f"\n"
        f"💬 신뢰도: {confidence_pct} ({grade}등급)"
    )


async def send_validation_notification(
    filename: str,
    error_count: int,
    warning_count: int,
    row_count: int,
    confidence: float,
    status: str,
) -> bool:
    """
    텔레그램으로 검증 결과 알림 발송.

    Returns:
        True: 전송 성공, False: 전송 실패 또는 미설정
    """
    if not is_configured():
        return False

    message = _build_message(
        filename=filename,
        error_count=error_count,
        warning_count=warning_count,
        row_count=row_count,
        confidence=confidence,
        status=status,
    )

    url = f"{TELEGRAM_API}/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload)
            if response.status_code == 200:
                return True
            else:
                print(f"Telegram API error: {response.status_code} - {response.text}")
                return False
    except Exception as e:
        print(f"Telegram notification failed: {e}")
        return False


async def send_test_notification() -> dict:
    """테스트 알림 발송."""
    if not is_configured():
        return {"success": False, "reason": "Telegram not configured (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)"}

    success = await send_validation_notification(
        filename="test_file.xlsx",
        error_count=0,
        warning_count=2,
        row_count=150,
        confidence=0.92,
        status="warning",
    )

    return {"success": success, "message": "Test notification sent" if success else "Failed to send"}
