"""
WIKISOFT4 백엔드 API 클라이언트

텔레그램 봇이 WIKISOFT4 검증 서버(기본 http://127.0.0.1:8004)와 통신하기 위한
얇은 HTTP 클라이언트.

Graceful Degradation:
- 백엔드가 꺼져 있거나 느려도 봇은 죽지 않는다
- 모든 실패는 BackendUnavailable 로 정규화되어 사용자에게 한국어로 안내된다
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx

from tg_bot.config import config

# WIKISOFT3 호환 경로 (인증 불필요, AuthMiddleware.PUBLIC_PATHS 에 포함)
HEALTH_PATH = "/api/health"
RECENT_RUNS_PATH = "/api/windmill/latest"


class BackendUnavailable(RuntimeError):
    """백엔드에 연결할 수 없거나 비정상 응답을 반환했을 때."""


def _parse_timestamp(value: Optional[str]) -> Optional[datetime]:
    """ISO8601 문자열 → datetime (실패 시 None)."""
    if not value:
        return None
    try:
        # 백엔드는 UTC ISO 문자열을 반환한다 ("...+00:00" 또는 "...Z")
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def _format_timestamp(value: Optional[str]) -> str:
    """표시용 시각 문자열 (로컬 타임존 기준 MM-DD HH:MM)."""
    parsed = _parse_timestamp(value)
    if parsed is None:
        return "시각 미상"
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone()
    return parsed.strftime("%m-%d %H:%M")


def _as_int(value: Any) -> int:
    """None/문자열 섞인 응답을 안전하게 int 로."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


@dataclass
class ValidationRun:
    """검증 이력 1건 (백엔드 응답 → 봇 표시용 정규화)."""

    run_id: str = ""
    timestamp: str = ""
    filename: str = ""
    company_name: str = ""
    status: str = ""
    action: str = ""
    message: str = ""
    confidence: Optional[float] = None
    error_count: int = 0
    warning_count: int = 0
    row_count: int = 0

    # action → 표시용 이모지/라벨
    _ACTION_LABELS = {
        "auto_approve": ("✅", "자동 승인"),
        "needs_review": ("⚠️", "검토 필요"),
        "rejected": ("❌", "검증 실패"),
    }

    @classmethod
    def from_api(cls, raw: Dict[str, Any]) -> "ValidationRun":
        """/api/windmill/latest 응답 1건을 변환."""
        return cls(
            run_id=raw.get("run_id") or "",
            timestamp=raw.get("timestamp") or "",
            # compat 라우터는 filename 을 file_url 키로 내려준다
            filename=raw.get("file_url") or raw.get("filename") or "이름 없음",
            company_name=raw.get("company_name") or "",
            status=raw.get("status") or "",
            action=raw.get("action") or "",
            message=raw.get("message") or "",
            confidence=raw.get("confidence"),
            error_count=_as_int(raw.get("error_count")),
            warning_count=_as_int(raw.get("warning_count")),
            row_count=_as_int(raw.get("row_count")),
        )

    @property
    def emoji(self) -> str:
        return self._ACTION_LABELS.get(self.action, ("📋", ""))[0]

    @property
    def label(self) -> str:
        return self._ACTION_LABELS.get(self.action, ("", self.status or "알 수 없음"))[1]

    @property
    def confidence_text(self) -> str:
        if self.confidence is None:
            return "-"
        return f"{self.confidence:.1%}"

    def summary_line(self) -> str:
        """/recent 목록용 한 줄 요약 (HTML)."""
        when = _format_timestamp(self.timestamp)
        return (
            f"{self.emoji} <code>{self.filename}</code>\n"
            f"   {when} · {self.label} · 오류 {self.error_count} / 경고 {self.warning_count}"
        )

    def detail_block(self) -> str:
        """/check 상세용 여러 줄 요약 (HTML)."""
        lines = [
            f"{self.emoji} <b>{self.label}</b>",
            f"📁 <code>{self.filename}</code>",
        ]
        if self.company_name:
            lines.append(f"🏢 {self.company_name}")
        lines.append(f"📊 오류 {self.error_count}건 / 경고 {self.warning_count}건")
        if self.row_count:
            lines.append(f"👥 {self.row_count}행")
        lines.append(f"🎯 신뢰도 {self.confidence_text}")
        lines.append(f"🕐 {_format_timestamp(self.timestamp)}")
        if self.message:
            lines.append(f"💬 {self.message}")
        return "\n".join(lines)


def summarize(runs: List[ValidationRun]) -> Dict[str, int]:
    """검증 이력 목록의 집계 (action 기준)."""
    return {
        "total": len(runs),
        "auto_approve": sum(1 for r in runs if r.action == "auto_approve"),
        "needs_review": sum(1 for r in runs if r.action == "needs_review"),
        "rejected": sum(1 for r in runs if r.action == "rejected"),
        "errors": sum(r.error_count for r in runs),
        "warnings": sum(r.warning_count for r in runs),
    }


class BackendClient:
    """WIKISOFT4 API 클라이언트."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        api_token: Optional[str] = None,
        timeout: Optional[float] = None,
        transport: Optional[httpx.AsyncBaseTransport] = None,
    ):
        self.base_url = (base_url or config.api_base_url).rstrip("/")
        self.api_key = api_key if api_key is not None else config.api_key
        self.api_token = api_token if api_token is not None else config.api_token
        self.timeout = timeout if timeout is not None else config.api_timeout
        # 테스트에서 httpx.MockTransport 를 주입하기 위한 훅
        self.transport = transport

    def _headers(self) -> Dict[str, str]:
        """선택적 인증 헤더. 둘 다 없으면 공개 경로로 접근한다."""
        headers: Dict[str, str] = {}
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers

    async def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """GET 요청 후 JSON 반환. 모든 실패는 BackendUnavailable 로."""
        url = f"{self.base_url}{path}"
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout, transport=self.transport
            ) as client:
                resp = await client.get(url, params=params, headers=self._headers())
        except httpx.TimeoutException as exc:
            raise BackendUnavailable(f"서버 응답 시간 초과 ({self.timeout:.0f}초)") from exc
        except httpx.HTTPError as exc:
            raise BackendUnavailable(f"서버에 연결할 수 없습니다: {exc}") from exc

        if resp.status_code in (401, 403):
            raise BackendUnavailable("인증에 실패했습니다 (WIKISOFT4_API_KEY 확인 필요)")
        if resp.status_code >= 400:
            raise BackendUnavailable(f"서버 오류 (HTTP {resp.status_code})")

        try:
            return resp.json()
        except ValueError as exc:
            raise BackendUnavailable("서버 응답을 해석할 수 없습니다") from exc

    async def health(self) -> Dict[str, Any]:
        """백엔드 헬스 체크. 실패 시 BackendUnavailable."""
        data = await self._get(HEALTH_PATH)
        if not isinstance(data, dict):
            raise BackendUnavailable("서버 응답 형식이 올바르지 않습니다")
        return data

    async def recent_runs(self, limit: int = 5) -> List[ValidationRun]:
        """최근 검증 이력 조회 (최신순)."""
        data = await self._get(RECENT_RUNS_PATH, params={"limit": limit})
        runs = data.get("runs") if isinstance(data, dict) else None
        if not isinstance(runs, list):
            return []
        return [ValidationRun.from_api(r) for r in runs if isinstance(r, dict)]

    async def latest_run(self) -> Optional[ValidationRun]:
        """가장 최근 검증 1건 (없으면 None)."""
        runs = await self.recent_runs(limit=1)
        return runs[0] if runs else None


# 기본 클라이언트 (핸들러에서 재사용)
def get_client() -> BackendClient:
    """설정 기반 기본 클라이언트 반환."""
    return BackendClient()
