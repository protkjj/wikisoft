"""
WIKISOFT4 백엔드 연결 테스트

httpx.MockTransport 로 백엔드를 대신하므로 네트워크가 필요 없다.
"""

import httpx
import pytest

from tg_bot.api_client import (
    BackendClient,
    BackendUnavailable,
    ValidationRun,
    summarize,
)

BASE_URL = "http://testserver:8004"

SAMPLE_RUNS = [
    {
        "timestamp": "2026-09-03T01:23:45+00:00",
        "action": "rejected",
        "confidence": 0.72,
        "message": "검증 실패: 3개 오류 발견",
        "run_id": "abc12345",
        "file_url": "명부_2026Q3.xlsx",
        "status": "error",
        "user_id": "u1",
        "company_name": "위키소프트",
        "error_count": 3,
        "warning_count": 1,
        "row_count": 120,
    },
    {
        "timestamp": "2026-09-02T09:00:00+00:00",
        "action": "auto_approve",
        "confidence": 0.97,
        "message": "자동 승인 (신뢰도 97.0%)",
        "run_id": "def67890",
        "file_url": "명부_2026Q2.xlsx",
        "status": "ok",
        "user_id": "u1",
        "company_name": None,
        "error_count": 0,
        "warning_count": 2,
        "row_count": 118,
    },
]


def make_client(handler, **kwargs) -> BackendClient:
    """MockTransport 를 주입한 클라이언트."""
    return BackendClient(
        base_url=BASE_URL,
        api_key="",
        api_token="",
        transport=httpx.MockTransport(handler),
        **kwargs,
    )


# ---------------------------------------------------------------- health

async def test_health_returns_payload():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/health"
        return httpx.Response(200, json={"status": "ok", "version": "4.1.0"})

    health = await make_client(handler).health()
    assert health["status"] == "ok"
    assert health["version"] == "4.1.0"


async def test_health_connection_error_becomes_backend_unavailable():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    with pytest.raises(BackendUnavailable, match="연결할 수 없습니다"):
        await make_client(handler).health()


async def test_timeout_becomes_backend_unavailable():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timed out", request=request)

    with pytest.raises(BackendUnavailable, match="시간 초과"):
        await make_client(handler).health()


async def test_server_error_becomes_backend_unavailable():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": "boom"})

    with pytest.raises(BackendUnavailable, match="HTTP 500"):
        await make_client(handler).health()


async def test_unauthorized_gives_auth_hint():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "unauthorized"})

    with pytest.raises(BackendUnavailable, match="인증"):
        await make_client(handler).health()


async def test_non_json_response_becomes_backend_unavailable():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="<html>not json</html>")

    with pytest.raises(BackendUnavailable, match="해석할 수 없습니다"):
        await make_client(handler).health()


# ------------------------------------------------------------ recent_runs

async def test_recent_runs_parses_and_passes_limit():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["limit"] = request.url.params.get("limit")
        return httpx.Response(200, json={"runs": SAMPLE_RUNS})

    runs = await make_client(handler).recent_runs(limit=5)

    assert seen["path"] == "/api/windmill/latest"
    assert seen["limit"] == "5"
    assert len(runs) == 2

    first = runs[0]
    assert first.filename == "명부_2026Q3.xlsx"  # file_url → filename 매핑
    assert first.company_name == "위키소프트"
    assert first.error_count == 3
    assert first.warning_count == 1
    assert first.row_count == 120
    assert first.action == "rejected"
    assert first.emoji == "❌"
    assert first.label == "검증 실패"
    assert first.confidence_text == "72.0%"


async def test_recent_runs_empty_history():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"runs": []})

    assert await make_client(handler).recent_runs() == []


async def test_recent_runs_tolerates_missing_runs_key():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"unexpected": True})

    assert await make_client(handler).recent_runs() == []


async def test_latest_run_returns_none_when_empty():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"runs": []})

    assert await make_client(handler).latest_run() is None


async def test_latest_run_returns_first():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"runs": SAMPLE_RUNS})

    run = await make_client(handler).latest_run()
    assert run is not None
    assert run.run_id == "abc12345"


# ----------------------------------------------------------------- auth

async def test_auth_headers_sent_when_configured():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["api_key"] = request.headers.get("X-API-Key")
        seen["authorization"] = request.headers.get("Authorization")
        return httpx.Response(200, json={"status": "ok"})

    client = BackendClient(
        base_url=BASE_URL,
        api_key="wk4_secret",
        api_token="jwt-token",
        transport=httpx.MockTransport(handler),
    )
    await client.health()

    assert seen["api_key"] == "wk4_secret"
    assert seen["authorization"] == "Bearer jwt-token"


async def test_no_auth_headers_when_unconfigured():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["api_key"] = request.headers.get("X-API-Key")
        seen["authorization"] = request.headers.get("Authorization")
        return httpx.Response(200, json={"status": "ok"})

    await make_client(handler).health()

    assert seen["api_key"] is None
    assert seen["authorization"] is None


async def test_trailing_slash_in_base_url_is_stripped():
    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url).startswith(f"{BASE_URL}/api/health")
        return httpx.Response(200, json={"status": "ok"})

    client = BackendClient(
        base_url=f"{BASE_URL}/",
        api_key="",
        api_token="",
        transport=httpx.MockTransport(handler),
    )
    await client.health()


# ------------------------------------------------------------- 표시 로직

def test_validation_run_defaults_for_sparse_payload():
    run = ValidationRun.from_api({})
    assert run.filename == "이름 없음"
    assert run.error_count == 0
    assert run.confidence_text == "-"
    assert run.emoji == "📋"


def test_validation_run_handles_null_counts():
    run = ValidationRun.from_api({"error_count": None, "warning_count": "2"})
    assert run.error_count == 0
    assert run.warning_count == 2


def test_summary_line_contains_key_facts():
    run = ValidationRun.from_api(SAMPLE_RUNS[0])
    line = run.summary_line()
    assert "명부_2026Q3.xlsx" in line
    assert "오류 3" in line
    assert "경고 1" in line


def test_detail_block_contains_key_facts():
    run = ValidationRun.from_api(SAMPLE_RUNS[0])
    block = run.detail_block()
    assert "검증 실패" in block
    assert "위키소프트" in block
    assert "120행" in block
    assert "72.0%" in block


def test_detail_block_omits_missing_company():
    run = ValidationRun.from_api(SAMPLE_RUNS[1])
    block = run.detail_block()
    assert "🏢" not in block


def test_summarize_counts_by_action():
    runs = [ValidationRun.from_api(r) for r in SAMPLE_RUNS]
    stats = summarize(runs)
    assert stats == {
        "total": 2,
        "auto_approve": 1,
        "needs_review": 0,
        "rejected": 1,
        "errors": 3,
        "warnings": 3,
    }
