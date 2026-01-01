"""
Slack 알림 스크립트
Windmill에서 Python 스크립트로 사용

검증 결과에 따라 Slack 채널에 알림 전송
"""

import requests
from typing import Optional


def main(
    webhook_url: str,
    action: str,
    confidence: float,
    message: str,
    file_name: Optional[str] = None,
    errors: Optional[list] = None,
    warnings: Optional[list] = None,
    ifrs_summary: Optional[dict] = None
) -> dict:
    """
    검증 결과를 Slack으로 알림합니다.

    Args:
        webhook_url: Slack Webhook URL
        action: 분기 결과 ("auto_approve" | "needs_review" | "rejected")
        confidence: 신뢰도 점수
        message: 결과 메시지
        file_name: 파일명 (선택)
        errors: 에러 목록 (선택)
        warnings: 경고 목록 (선택)
        ifrs_summary: IFRS 계산 결과 요약 (선택)

    Returns:
        dict: {"success": bool, "message": str}
    """

    # 아이콘 및 색상 결정
    if action == "auto_approve":
        icon = "✅"
        color = "#36a64f"  # 녹색
        title = "자동 승인 완료"
    elif action == "needs_review":
        icon = "⚠️"
        color = "#ffcc00"  # 노란색
        title = "수동 검토 필요"
    else:  # rejected
        icon = "❌"
        color = "#ff0000"  # 빨간색
        title = "검증 실패"

    # 메시지 블록 구성
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"{icon} WIKISOFT3 검증 결과"
            }
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*상태:*\n{title}"},
                {"type": "mrkdwn", "text": f"*신뢰도:*\n{confidence:.1%}"}
            ]
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*메시지:*\n{message}"}
        }
    ]

    # 파일명 추가
    if file_name:
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*파일:*\n`{file_name}`"}
        })

    # 에러 추가
    if errors:
        error_text = "\n".join([f"• {e.get('message', str(e))}" for e in errors[:5]])
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*에러 ({len(errors)}건):*\n{error_text}"}
        })

    # 경고 추가
    if warnings:
        warning_text = "\n".join([f"• {w.get('message', str(w))}" for w in warnings[:5]])
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*경고 ({len(warnings)}건):*\n{warning_text}"}
        })

    # IFRS 결과 추가
    if ifrs_summary:
        dbo = ifrs_summary.get("total_dbo", 0)
        blocks.append({
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*퇴직급여 부채(DBO):*\n₩{dbo:,.0f}"},
                {"type": "mrkdwn", "text": f"*직원 수:*\n{ifrs_summary.get('employee_count', 0)}명"}
            ]
        })

    # Slack 전송
    try:
        response = requests.post(
            webhook_url,
            json={"blocks": blocks},
            timeout=10
        )
        response.raise_for_status()
        return {"success": True, "message": "Slack 알림 전송 완료"}
    except Exception as e:
        return {"success": False, "message": f"Slack 전송 실패: {str(e)}"}
