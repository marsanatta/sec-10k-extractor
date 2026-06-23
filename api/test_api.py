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


def test_extract_returns_full_shape(client, monkeypatch):
    monkeypatch.setenv("SEC_EDGAR_USER_AGENT", "Test Runner test@example.com")
    monkeypatch.setattr(server.pipeline, "extract", lambda **kw: _fake_result())

    resp = client.post("/api/extract", json={"accession": "0000320193-24-000123"})
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
    calls = {"n": 0}

    def _counting_extract(**kw):
        calls["n"] += 1
        return _fake_result()

    monkeypatch.setattr(server.pipeline, "extract", _counting_extract)
    client.post("/api/extract", json={"accession": "0000320193-24-000123"})
    client.post("/api/extract", json={"accession": "0000320193-24-000123"})
    assert calls["n"] == 1


def test_extract_missing_input_returns_400(client, monkeypatch):
    monkeypatch.setenv("SEC_EDGAR_USER_AGENT", "Test Runner test@example.com")
    resp = client.post("/api/extract", json={})
    assert resp.status_code == 400
    assert "error" in resp.json()


def test_extract_missing_env_returns_500(client, monkeypatch):
    monkeypatch.delenv("SEC_EDGAR_USER_AGENT", raising=False)
    resp = client.post("/api/extract", json={"accession": "x"})
    assert resp.status_code == 500
    assert "SEC_EDGAR_USER_AGENT" in resp.json()["error"]


def test_extract_timeout_returns_504(client, monkeypatch):
    import time

    monkeypatch.setenv("SEC_EDGAR_USER_AGENT", "Test Runner test@example.com")
    monkeypatch.setattr(server, "EXTRACT_TIMEOUT_S", 0.1)
    monkeypatch.setattr(server.pipeline, "extract", lambda **kw: time.sleep(1) or _fake_result())
    resp = client.post("/api/extract", json={"accession": "slow"})
    assert resp.status_code == 504
    assert "timed out" in resp.json()["error"]


def test_extract_failure_returns_structured_error(client, monkeypatch):
    monkeypatch.setenv("SEC_EDGAR_USER_AGENT", "Test Runner test@example.com")

    def _boom(**kw):
        raise ValueError("no filing found")

    monkeypatch.setattr(server.pipeline, "extract", _boom)
    resp = client.post("/api/extract", json={"accession": "bad"})
    assert resp.status_code == 502
    assert "Extraction failed" in resp.json()["error"]
