from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api import server
from sec10k.schema import (
    Band,
    Confidence,
    ExtractionResult,
    FilingMeta,
    Item,
    Provenance,
    Status,
)


TOKEN = "test-access-token"
AUTH = {"Authorization": f"Bearer {TOKEN}"}


@pytest.fixture(autouse=True)
def _clear_cache():
    server._cache.clear()
    yield
    server._cache.clear()


@pytest.fixture
def client():
    return TestClient(server.app)


def _fake_result() -> ExtractionResult:
    meta = FilingMeta(
        cik="320193", accession="0000320193-24-000123", company="Apple Inc.",
        form="10-K", filing_date="2024-11-01", fiscal_year=2024, format_era="ixbrl",
        primary_document="aapl.htm", source_url="https://example.com/aapl.htm",
        smaller_reporting=False,
    )
    item = Item(
        item_id="I.1", part="I", item="1", title="Business", text="Our business...",
        char_range=(0, 14), status=Status.PRESENT,
        confidence=Confidence(Band.HIGH, 0.9, ["round_trip"]),
        provenance=Provenance(["anchor"], ["round_trip"], []),
    )
    return ExtractionResult(
        meta=meta, items=[item], canonical_text_len=14,
        summary={"needs_review": False, "coverage_fraction": 0.95},
        canonical_text="Our business..",
    )


def test_health_is_open(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_demo_returns_five_entries(client):
    resp = client.get("/api/demo")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 5
    assert {e["id"] for e in body} == {
        "apple-fy2024", "ko-fy2023", "ge-fy2023", "m2i-fy2023", "msft-fy1995"
    }


def test_eval_returns_markdown(client):
    resp = client.get("/api/eval")
    assert resp.status_code == 200
    assert "markdown" in resp.json()
    assert isinstance(resp.json()["markdown"], str)


def test_demo_result_is_open_without_token(client, monkeypatch):
    monkeypatch.setenv("SEC_EDGAR_USER_AGENT", "Test Runner test@example.com")
    monkeypatch.setenv("SEC10K_ACCESS_TOKEN", TOKEN)  # gate set, but demo path bypasses it
    monkeypatch.setattr(server.pipeline, "extract", lambda **kw: _fake_result())
    resp = client.get("/api/demo-result/apple-fy2024")  # no Authorization header
    assert resp.status_code == 200
    assert resp.json()["items"][0]["status"] == "present"


def test_demo_result_unknown_id_returns_404(client, monkeypatch):
    monkeypatch.setenv("SEC_EDGAR_USER_AGENT", "Test Runner test@example.com")
    resp = client.get("/api/demo-result/nope")
    assert resp.status_code == 404
    assert "error" in resp.json()


def test_extract_text_requires_token(client, monkeypatch):
    monkeypatch.setenv("SEC10K_ACCESS_TOKEN", TOKEN)
    resp = client.post("/api/extract-text", json={"text": "Item 1. Business"})  # no auth header
    assert resp.status_code == 401


def test_extract_text_empty_returns_400(client, monkeypatch):
    monkeypatch.setenv("SEC10K_ACCESS_TOKEN", TOKEN)
    resp = client.post("/api/extract-text", json={"text": "   "}, headers=AUTH)
    assert resp.status_code == 400


def test_extract_text_runs_offline(client, monkeypatch):
    # No network, no pipeline monkeypatch: this exercises the real offline segmentation path.
    monkeypatch.setenv("SEC10K_ACCESS_TOKEN", TOKEN)
    body_text = (
        "PART I\n\nITEM 1. BUSINESS\nWe design and sell widgets.\n\n"
        "ITEM 1A. RISK FACTORS\nOur business faces risks.\n\n"
        "ITEM 2. PROPERTIES\nWe lease offices.\n"
    )
    resp = client.post("/api/extract-text", json={"text": body_text}, headers=AUTH)
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body["items"], list)
    assert body["canonical_text"].startswith("PART I")


def test_gate_not_bypassable_via_path_variants(client, monkeypatch):
    # The gate matches by path prefix; pin that path forms which evade the literal prefix also
    # never reach the protected handler (404/405/401), so a future routing change can't open it.
    monkeypatch.setenv("SEC10K_ACCESS_TOKEN", TOKEN)
    for path in ("//api/extract", "/API/extract", "/api/extract/", "/api/extract-text"):
        resp = client.post(path, json={"accession": "x"})  # no Authorization header
        assert resp.status_code != 200, path


def test_extract_text_too_large_returns_413(client, monkeypatch):
    monkeypatch.setenv("SEC10K_ACCESS_TOKEN", TOKEN)
    big = "a" * (server.MAX_UPLOAD_CHARS + 1)
    resp = client.post("/api/extract-text", json={"text": big}, headers=AUTH)
    assert resp.status_code == 413


def test_extract_text_makes_no_network_call(client, monkeypatch):
    monkeypatch.setenv("SEC10K_ACCESS_TOKEN", TOKEN)

    def _boom(*a, **k):
        raise AssertionError("upload path must not hit the network")

    monkeypatch.setattr(server.pipeline, "fetch_xbrl_facts", _boom)
    resp = client.post(
        "/api/extract-text", json={"text": "PART I\nITEM 1. BUSINESS\nx\n"}, headers=AUTH
    )
    assert resp.status_code == 200


def test_extract_returns_full_shape(client, monkeypatch):
    monkeypatch.setenv("SEC_EDGAR_USER_AGENT", "Test Runner test@example.com")
    monkeypatch.setenv("SEC10K_ACCESS_TOKEN", TOKEN)
    monkeypatch.setattr(server.pipeline, "extract", lambda **kw: _fake_result())

    resp = client.post("/api/extract", json={"accession": "0000320193-24-000123"}, headers=AUTH)
    assert resp.status_code == 200
    body = resp.json()
    assert body["meta"]["accession"] == "0000320193-24-000123"
    assert body["canonical_text"] == "Our business.."
    assert body["items"][0]["status"] == "present"
    assert body["items"][0]["confidence"]["band"] == "high"
    assert body["items"][0]["char_range"] == [0, 14]
    assert body["summary"]["needs_review"] is False


def test_extract_caches_by_accession(client, monkeypatch):
    monkeypatch.setenv("SEC_EDGAR_USER_AGENT", "Test Runner test@example.com")
    monkeypatch.setenv("SEC10K_ACCESS_TOKEN", TOKEN)
    calls = {"n": 0}

    def _counting_extract(**kw):
        calls["n"] += 1
        return _fake_result()

    monkeypatch.setattr(server.pipeline, "extract", _counting_extract)
    client.post("/api/extract", json={"accession": "0000320193-24-000123"}, headers=AUTH)
    client.post("/api/extract", json={"accession": "0000320193-24-000123"}, headers=AUTH)
    assert calls["n"] == 1


def test_extract_missing_input_returns_400(client, monkeypatch):
    monkeypatch.setenv("SEC_EDGAR_USER_AGENT", "Test Runner test@example.com")
    monkeypatch.setenv("SEC10K_ACCESS_TOKEN", TOKEN)
    resp = client.post("/api/extract", json={}, headers=AUTH)
    assert resp.status_code == 400
    assert "error" in resp.json()


def test_extract_missing_env_returns_500(client, monkeypatch):
    monkeypatch.delenv("SEC_EDGAR_USER_AGENT", raising=False)
    monkeypatch.setenv("SEC10K_ACCESS_TOKEN", TOKEN)
    resp = client.post("/api/extract", json={"accession": "x"}, headers=AUTH)
    assert resp.status_code == 500
    assert "SEC_EDGAR_USER_AGENT" in resp.json()["error"]


def test_extract_gate_unconfigured_returns_503(client, monkeypatch):
    monkeypatch.delenv("SEC10K_ACCESS_TOKEN", raising=False)
    resp = client.post("/api/extract", json={"accession": "x"})
    assert resp.status_code == 503
    assert "SEC10K_ACCESS_TOKEN" in resp.json()["error"]


def test_extract_wrong_token_returns_401(client, monkeypatch):
    monkeypatch.setenv("SEC10K_ACCESS_TOKEN", TOKEN)
    resp = client.post(
        "/api/extract", json={"accession": "x"}, headers={"Authorization": "Bearer wrong"}
    )
    assert resp.status_code == 401


def test_extract_absent_token_returns_401(client, monkeypatch):
    monkeypatch.setenv("SEC10K_ACCESS_TOKEN", TOKEN)
    resp = client.post("/api/extract", json={"accession": "x"})
    assert resp.status_code == 401


def test_extract_timeout_returns_504(client, monkeypatch):
    import time

    monkeypatch.setenv("SEC_EDGAR_USER_AGENT", "Test Runner test@example.com")
    monkeypatch.setenv("SEC10K_ACCESS_TOKEN", TOKEN)
    monkeypatch.setattr(server, "EXTRACT_TIMEOUT_S", 0.1)
    monkeypatch.setattr(server.pipeline, "extract", lambda **kw: time.sleep(1) or _fake_result())
    resp = client.post("/api/extract", json={"accession": "slow"}, headers=AUTH)
    assert resp.status_code == 504
    assert "timed out" in resp.json()["error"]


def test_extract_failure_returns_structured_error(client, monkeypatch):
    monkeypatch.setenv("SEC_EDGAR_USER_AGENT", "Test Runner test@example.com")
    monkeypatch.setenv("SEC10K_ACCESS_TOKEN", TOKEN)

    def _boom(**kw):
        raise ValueError("no filing found")

    monkeypatch.setattr(server.pipeline, "extract", _boom)
    resp = client.post("/api/extract", json={"accession": "bad"}, headers=AUTH)
    assert resp.status_code == 502
    assert "Extraction failed" in resp.json()["error"]
