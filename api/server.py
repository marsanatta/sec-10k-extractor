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
from sec10k.normalize import to_canonical

REPO_ROOT = Path(__file__).resolve().parent.parent
WEB_DIST = REPO_ROOT / "web" / "dist"
EVAL_REPORT = REPO_ROOT / "eval" / "report.md"

# Extraction is slow (GE is ~4MB); cap it so a wedged fetch never holds the worker forever.
EXTRACT_TIMEOUT_S = 120

# Cap pasted/uploaded filing text so a public endpoint can't be made to segment unbounded input.
MAX_UPLOAD_CHARS = 6_000_000
_HTML_RE = re.compile(r"<\s*(html|body|div|p|table|td|tr|span|ix:)\b", re.I)

# Curated reviewer examples. Extraction still goes through /api/extract (and is cached by
# accession), so a clean filer fetched by ticker resolves to the same cached result.
DEMO_FILINGS = [
    {"id": "apple-fy2024", "label": "Apple FY2024", "accession": "0000320193-24-000123",
     "note": "clean iXBRL"},
    {"id": "ko-fy2023", "label": "Coca-Cola FY2023", "ticker": "KO", "fiscal_year": 2023,
     "note": "clean iXBRL"},
    {"id": "ge-fy2023", "label": "General Electric FY2023", "accession": "0000040545-24-000027",
     "note": "known mis-segmented - regex latched onto the cross-reference index"},
    {"id": "m2i-fy2023", "label": "M2i Global FY2023", "accession": "0001493152-24-014827",
     "note": "newline-broken 'Item' headers defeat the regex; unlocated items are flagged "
             "extraction_failure (not dropped) and the filing needs review"},
    {"id": "msft-fy1995", "label": "Microsoft FY1995", "accession": "0000891020-95-000433",
     "note": "legacy SGML"},
]

_cache: dict[str, dict] = {}
_pool = ThreadPoolExecutor(max_workers=4)

app = FastAPI(title="SEC 10-K Extractor")
app.add_middleware(TokenAuthMiddleware)


class ExtractRequest(BaseModel):
    ticker: str | None = None
    fiscal_year: int | None = None
    accession: str | None = None


@app.get("/api/demo")
def demo() -> list[dict]:
    return DEMO_FILINGS


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/eval")
def eval_report() -> dict:
    if not EVAL_REPORT.exists():
        return {"markdown": "_No eval report found._"}
    return {"markdown": EVAL_REPORT.read_text(encoding="utf-8")}


def _run_extraction(ticker, fiscal_year, accession) -> JSONResponse:
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

    cache_key = accession or f"{ticker}:{fiscal_year}"
    if cache_key in _cache:
        return JSONResponse(content=_cache[cache_key])

    future = _pool.submit(
        pipeline.extract, ticker_or_cik=ticker, fiscal_year=fiscal_year, accession=accession,
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
        _cache[real_accession] = payload
    return JSONResponse(content=payload)


@app.post("/api/extract")
def extract(req: ExtractRequest) -> JSONResponse:
    return _run_extraction(req.ticker, req.fiscal_year, req.accession)


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
    canonical, era = _canonical_from_upload(text)
    future = _pool.submit(pipeline.extract_from_text, canonical, era)
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
