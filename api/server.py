from __future__ import annotations

import os
import re
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from dataclasses import asdict
from pathlib import Path

from bs4 import BeautifulSoup
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from api.security import TokenAuthMiddleware
from sec10k import pipeline
from sec10k.ingest import RawFiling
from sec10k.llm_models import DEFAULT_MODEL, FALLBACK_MODELS
from sec10k.normalize import to_canonical

REPO_ROOT = Path(__file__).resolve().parent.parent
WEB_DIST = REPO_ROOT / "web" / "dist"
EVAL_REPORT = REPO_ROOT / "eval" / "report.md"

# Extraction is slow (GE is ~4MB); cap it so a wedged fetch never holds the worker forever.
EXTRACT_TIMEOUT_S = 120

# Cap pasted/uploaded filing text so a public endpoint can't be made to segment unbounded input.
MAX_UPLOAD_CHARS = 6_000_000
_HTML_RE = re.compile(r"<\s*(html|body|div|p|table|td|tr|span|ix:)\b", re.I)

# Curated reviewer examples, grouped into "Works well" (good) and "Known limitations"
# (limitation) per the README tables / ANALYSIS.md sec.6. Extraction still goes through
# /api/extract (and is cached by accession), so a clean filer fetched by ticker resolves to
# the same cached result. `detail` is the rich, English-only description shown in the gallery.
DEMO_FILINGS = [
    {"id": "apple-fy2024", "label": "Apple FY2024", "accession": "0000320193-24-000123",
     "group": "good", "note": "clean iXBRL",
     "detail": "Clean modern iXBRL. All items found; char-exact boundary match (IoU 1.0)."},
    {"id": "ko-fy2023", "label": "Coca-Cola FY2023", "accession": "0000021344-24-000009",
     "group": "good", "note": "clean iXBRL",
     "detail": "Clean modern iXBRL. All items found; char-exact boundary match (IoU 1.0)."},
    {"id": "msft-fy2023", "label": "Microsoft FY2023", "accession": "0000950170-23-035122",
     "group": "good", "note": "clean iXBRL",
     "detail": "Clean modern iXBRL. All items found; char-exact boundary match (IoU 1.0)."},
    {"id": "msft-fy1995", "label": "Microsoft FY1995", "accession": "0000891020-95-000433",
     "group": "good", "note": "legacy SGML",
     "detail": "Legacy SGML (pre-2001). Items found; carries human-verified boundary gold "
               "(IoU 1.0 on items 1/2/7)."},
    {"id": "msft-fy1996", "label": "Microsoft FY1996", "accession": "0000891020-96-001130",
     "group": "good", "note": "legacy SGML",
     "detail": "Legacy SGML (pre-2001). Items found; era-absent items such as 7A are correctly "
               "marked legitimately-absent, not extraction failures."},
    {"id": "ge-fy2009", "label": "General Electric FY2009", "accession": "0000040545-10-000010",
     "group": "good", "note": "HTML collapsed body, fallback recovers",
     "detail": "HTML era with a collapsed body. The rules collapse the body, then the "
               "edgartools fallback rebuilds the items."},
    {"id": "m2i-fy2023", "label": "M2i Global FY2023", "accession": "0001493152-24-014827",
     "group": "good", "note": "token-per-line headers, recovered",
     "detail": "Token-per-line headers ('Item' and '1.' on separate lines). A newline-tolerant "
               "rule recovers the items."},
    {"id": "scwo-fy2025", "label": "374Water FY2025", "accession": "0001654954-26-003094",
     "group": "good", "note": "SRC token-per-line headers, recovered",
     "detail": "Smaller-reporting-company full 10-K with token-per-line headers; recovered by "
               "newline tolerance."},
    {"id": "jpm-fy2023", "label": "JPMorgan FY2023", "accession": "0000019617-24-000225",
     "group": "good", "note": "broken text extractor, HTML fallback recovers",
     "detail": "A broken text extractor is detected and the HTML fallback recovers the items. "
               "Note: Item 7 (MD&A) is scattered - a tracked boundary limitation, where the "
               "span is a pointer stub and the real MD&A falls outside it."},
    {"id": "ms-fy2024", "label": "Morgan Stanley FY2024", "accession": "0000895421-25-000304",
     "group": "limitation", "note": "header text stripped - the named ceiling",
     "detail": "Header text stripped - the named ceiling. The 'Item N' labels live only in "
               "styled tags that are removed when the styling is stripped, so both the rule and "
               "the fallback find 0 items. Unsupported without a non-header model. Flagged "
               "(needs_review), never silent."},
    {"id": "intc-fy2018", "label": "Intel FY2018", "accession": "0000050863-19-000007",
     "group": "limitation", "note": "cross-reference index, ~1-2% coverage",
     "detail": "Cross-reference index. The body has no 'Item N' headings; items are listed only "
               "in an end-of-document index table, so coverage drops to ~1-2%. Unsupported by "
               "the header approach (~1% of filings). Flagged."},
    {"id": "ge-fy2023", "label": "General Electric FY2023", "accession": "0000040545-24-000027",
     "group": "limitation", "note": "cross-reference index, ~1% coverage",
     "detail": "Cross-reference index. Integrated MD&A plus out-of-order item references give "
               "~1% coverage; caught (needs_review), but not boundary-goldable by hand."},
    {"id": "bac-fy2023", "label": "Bank of America FY2023", "accession": "0000070858-24-000122",
     "group": "limitation", "note": "lead-item drop (run-fragmentation)",
     "detail": "Lead-item drop. Item 1 and Item 7 are dropped due to run-fragmentation. "
               "Flagged."},
    {"id": "wmt-fy2003", "label": "Walmart FY2003", "accession": "0000104169-03-000005",
     "group": "limitation", "note": "lead-item drop (joined header line)",
     "detail": "Lead-item drop. A joined-together 'PART I ITEM 1.' line defeats the line-start "
               "anchor and drops Item 1. Flagged."},
    {"id": "hon-fy2024", "label": "Honeywell FY2024", "accession": "0000773840-25-000010",
     "group": "limitation", "note": "lead-item drop (no-separator header)",
     "detail": "Lead-item drop. A no-separator header ('ITEM 1 BUSINESS' with no '.'/':' "
               "separator) is not matched. Flagged."},
    {"id": "gis-fy2018", "label": "General Mills FY2018", "accession": "0001193125-18-209377",
     "group": "limitation", "note": "separator-less header (char-gold-verified)",
     "detail": "Separator-less header (hard anchor). The boundary is char-gold-verified, but "
               "the filing is still tracked at the full-filing level. Tracked."},
    {"id": "scwo-fy2025-amend", "label": "374Water FY2025 (10-K/A)",
     "accession": "0001654954-26-004179",
     "group": "limitation", "note": "filing selection (amendment vs full 10-K)",
     "detail": "Filing selection. A ticker-by-year lookup can return a 10-K/A amendment "
               "(Part III only) instead of the full 10-K. The eval pins the full filing by "
               "accession. Tracked."},
]

_cache: dict[str, dict] = {}
_pool = ThreadPoolExecutor(max_workers=4)
_models_cache: list[dict] | None = None

app = FastAPI(title="SEC 10-K Extractor")
app.add_middleware(TokenAuthMiddleware)


def _models() -> list[dict]:
    """Live Copilot model list (cached per process), falling back to the static snapshot when no
    token / SDK is available so the picker and validation work in the $0 path."""
    global _models_cache
    if _models_cache is None:
        try:
            from sec10k.copilot_client import list_models_sync

            _models_cache = list_models_sync()
        except Exception:
            _models_cache = FALLBACK_MODELS
    return _models_cache


def _model_error(model: str | None) -> JSONResponse | None:
    if model and model not in {m["id"] for m in _models()}:
        return JSONResponse(status_code=400, content={"error": f"Unknown model: {model}"})
    return None


class ExtractRequest(BaseModel):
    ticker: str | None = None
    fiscal_year: int | None = None
    accession: str | None = None
    model: str | None = None
    escalate: bool = False


@app.get("/api/demo")
def demo() -> list[dict]:
    return DEMO_FILINGS


@app.get("/api/models")
def models() -> dict:
    """The escalation-tier model picker's options + the default. Live list when a Copilot token is
    configured, else the static fallback. Open (no token gate) -- it leaks no filing data."""
    return {"models": _models(), "default": DEFAULT_MODEL}


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/eval")
def eval_report() -> dict:
    if not EVAL_REPORT.exists():
        return {"markdown": "_No eval report found._"}
    return {"markdown": EVAL_REPORT.read_text(encoding="utf-8")}


def _run_extraction(ticker, fiscal_year, accession, model=None, escalate: bool = False) -> JSONResponse:
    if not os.environ.get("SEC_EDGAR_USER_AGENT", "").strip():
        return JSONResponse(
            status_code=500,
            content={"error": "SEC_EDGAR_USER_AGENT is not set on the server. SEC requires a "
                              "descriptive User-Agent such as 'Jane Doe jane@example.com'."},
        )
    if not accession and not ticker:
        return JSONResponse(
            status_code=400,
            content={"error": "Provide an accession, or a ticker (with optional fiscal_year)."},
        )
    if (err := _model_error(model)) is not None:
        return err

    # The escalation tier (and its model) can move boundaries, so it is part of the cache identity.
    # Off-requests share one entry; on-requests key by model.
    suffix = f"|on:{model or DEFAULT_MODEL}" if escalate else "|off"
    cache_key = (accession or f"{ticker}:{fiscal_year}") + suffix
    if cache_key in _cache:
        return JSONResponse(content=_cache[cache_key])

    future = _pool.submit(
        pipeline.extract, ticker_or_cik=ticker, fiscal_year=fiscal_year, accession=accession,
        llm_model=model, llm_enabled=escalate,
    )
    try:
        result = future.result(timeout=EXTRACT_TIMEOUT_S)
    except FutureTimeout:
        return JSONResponse(
            status_code=504,
            content={"error": f"Extraction timed out after {EXTRACT_TIMEOUT_S}s."},
        )
    except Exception as exc:  # network/parse failures must not crash the server
        return JSONResponse(status_code=502, content={"error": f"Extraction failed: {exc}"})

    payload = asdict(result)
    # cache by the real accession so a ticker lookup and a later accession lookup share it
    real_accession = payload["meta"]["accession"]
    _cache[cache_key] = payload
    if real_accession:
        _cache[real_accession + suffix] = payload
    return JSONResponse(content=payload)


@app.post("/api/extract")
def extract(req: ExtractRequest) -> JSONResponse:
    return _run_extraction(req.ticker, req.fiscal_year, req.accession, req.model, req.escalate)


@app.get("/api/demo-result/{demo_id}")
def demo_result(demo_id: str) -> JSONResponse:
    """Open (ungated) extraction for the fixed curated demo set. The token gate exists to stop
    arbitrary EDGAR queries; the demos are a small fixed list (not user input), so reviewers
    can browse them without a token. Cached after the first hit like any other extraction."""
    entry = next((d for d in DEMO_FILINGS if d["id"] == demo_id), None)
    if entry is None:
        return JSONResponse(status_code=404, content={"error": f"Unknown demo id: {demo_id}"})
    return _run_extraction(entry.get("ticker"), entry.get("fiscal_year"), entry.get("accession"))


class ExtractTextRequest(BaseModel):
    text: str
    model: str | None = None
    escalate: bool = False


def _canonical_from_upload(raw_text: str) -> tuple[str, str]:
    """Normalise pasted/uploaded filing text into the same canonical form an EDGAR fetch
    produces, so offsets and segmentation behave identically. HTML is stripped to text first."""
    if _HTML_RE.search(raw_text):
        plain, html = BeautifulSoup(raw_text, "html.parser").get_text("\n"), raw_text
    else:
        plain, html = raw_text, None
    raw = RawFiling(
        cik="", accession="", company="(uploaded)", form="10-K", filing_date="",
        period_of_report=None, primary_document=None, source_url=None,
        smaller_reporting=None, html=html, text=plain,
    )
    return to_canonical(raw)


@app.post("/api/extract-text")
def extract_text(req: ExtractTextRequest) -> JSONResponse:
    """Run the offline pipeline on pasted/uploaded filing text (no EDGAR fetch). Enables
    submitting an arbitrary filing AND mutation testing -- paste a filing, delete/reorder/
    truncate an Item, and watch the validation layer flag it. Gated like /api/extract (it is
    under that path prefix): user-supplied compute on a public URL needs the shared token."""
    text = req.text or ""
    if not text.strip():
        return JSONResponse(status_code=400, content={"error": "Provide filing text to extract."})
    if len(text) > MAX_UPLOAD_CHARS:
        return JSONResponse(
            status_code=413,
            content={"error": f"Text too large (> {MAX_UPLOAD_CHARS:,} chars)."},
        )
    if (err := _model_error(req.model)) is not None:
        return err
    canonical, era = _canonical_from_upload(text)
    future = _pool.submit(
        pipeline.extract_from_text, canonical, era, llm_model=req.model, llm_enabled=req.escalate
    )
    try:
        result = future.result(timeout=EXTRACT_TIMEOUT_S)
    except FutureTimeout:
        return JSONResponse(
            status_code=504,
            content={"error": f"Extraction timed out after {EXTRACT_TIMEOUT_S}s."},
        )
    except Exception as exc:
        return JSONResponse(status_code=502, content={"error": f"Extraction failed: {exc}"})
    return JSONResponse(content=asdict(result))


if WEB_DIST.exists():
    app.mount("/", StaticFiles(directory=str(WEB_DIST), html=True), name="web")
