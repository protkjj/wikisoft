"""
핸들러 렌더링 테스트 — 백엔드 연결 성공/실패 두 경로 모두 확인.
"""

import httpx
import pytest

from tg_bot import handlers
from tg_bot.api_client import BackendClient

from tests.test_api_client import BASE_URL, SAMPLE_RUNS


def patch_backend(monkeypatch, handler):
    """handlers 가 쓰는 클라이언트를 MockTransport 버전으로 교체."""
    def _factory() -> BackendClient:
        return BackendClient(
            base_url=BASE_URL,
            api_key="",
            api_token="",
            transport=httpx.MockTransport(handler),
        )

    monkeypatch.setattr(handlers, "get_client", _factory)


def route(request: httpx.Request) -> httpx.Response:
    """정상 동작하는 백엔드."""
    if request.url.path == "/api/health":
        return httpx.Response(200, json={"status": "ok", "version": "4.1.0"})
    if request.url.path == "/api/windmill/latest":
        return httpx.Response(200, json={"runs": SAMPLE_RUNS})
    return httpx.Response(404, json={"error": "not_found"})


def route_empty(request: httpx.Request) -> httpx.Response:
    """이력이 아직 없는 백엔드."""
    if request.url.path == "/api/health":
        return httpx.Response(200, json={"status": "ok", "version": "4.1.0"})
    return httpx.Response(200, json={"runs": []})


def route_down(request: httpx.Request) -> httpx.Response:
    """꺼져 있는 백엔드."""
    raise httpx.ConnectError("connection refused", request=request)


# ------------------------------------------------------------- /recent

async def test_render_recent_lists_runs(monkeypatch):
    patch_backend(monkeypatch, route)
    text = await handlers._render_recent()

    assert "최근 검증 결과" in text
    assert "명부_2026Q3.xlsx" in text
    assert "명부_2026Q2.xlsx" in text
    assert "오류 3" in text


async def test_render_recent_empty_history(monkeypatch):
    patch_backend(monkeypatch, route_empty)
    text = await handlers._render_recent()

    assert "아직 검증 이력이 없습니다" in text


async def test_render_recent_degrades_when_backend_down(monkeypatch):
    patch_backend(monkeypatch, route_down)
    text = await handlers._render_recent()

    assert "서버 연결 실패" in text
    assert "WIKISOFT4 서버가 실행 중인지" in text


# -------------------------------------------------------------- /check

async def test_render_status_shows_health_and_summary(monkeypatch):
    patch_backend(monkeypatch, route)
    text = await handlers._render_status()

    assert "서버 연결: ✅ 정상 (v4.1.0)" in text
    assert "자동 승인 1건" in text
    assert "검증 실패 1건" in text
    assert "마지막 검증" in text
    assert "명부_2026Q3.xlsx" in text


async def test_render_status_empty_history(monkeypatch):
    patch_backend(monkeypatch, route_empty)
    text = await handlers._render_status()

    assert "서버 연결: ✅ 정상" in text
    assert "아직 검증 이력이 없습니다" in text


async def test_render_status_degrades_when_backend_down(monkeypatch):
    patch_backend(monkeypatch, route_down)
    text = await handlers._render_status()

    assert "서버 연결 실패" in text


async def test_render_status_survives_history_failure(monkeypatch):
    """헬스는 정상인데 이력 조회만 실패하는 경우."""
    def route_partial(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/health":
            return httpx.Response(200, json={"status": "ok", "version": "4.1.0"})
        return httpx.Response(500, json={"error": "boom"})

    patch_backend(monkeypatch, route_partial)
    text = await handlers._render_status()

    assert "서버 연결: ✅ 정상" in text
    assert "검증 이력을 불러오지 못했습니다" in text
