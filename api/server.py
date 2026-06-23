from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from dataclasses import asdict
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from sec10k import pipeline

REPO_ROOT = Path(__file__).resolve().parent.parent
WEB_DIST = REPO_ROOT / "web" / "dist"
EVAL_REPORT = REPO_ROOT / "eval" / "report.md"

# Extraction is slow (GE is ~4MB); cap it so a wedged fetch never holds the worker forever.
EXTRACT_TIMEOUT_S = 120

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


class ExtractRequest(BaseModel):
    ticker: str | None = None
    fiscal_year: int | None = None
    accession: str | None = None


@app.get("/api/demo")
def demo() -> list[dict]:
    return DEMO_FILINGS


@app.get("/api/eval")
def eval_report() -> dict:
    if not EVAL_REPORT.exists():
        return {"markdown": "_No eval report found._"}
    return {"markdown": EVAL_REPORT.read_text(encoding="utf-8")}


@app.post("/api/extract")
def extract(req: ExtractRequest) -> JSONResponse:
    if not os.environ.get("SEC_EDGAR_USER_AGENT", "").strip():
        return JSONResponse(
            status_code=500,
            content={"error": "SEC_EDGAR_USER_AGENT is not set on the server. SEC requires a "
                              "descriptive User-Agent such as 'Jane Doe jane@example.com'."},
        )
    if not req.accession and not req.ticker:
        return JSONResponse(
            status_code=400,
            content={"error": "Provide an accession, or a ticker (with optional fiscal_year)."},
        )

    cache_key = req.accession or f"{req.ticker}:{req.fiscal_year}"
    if cache_key in _cache:
        return JSONResponse(content=_cache[cache_key])

    future = _pool.submit(
        pipeline.extract,
        ticker_or_cik=req.ticker, fiscal_year=req.fiscal_year, accession=req.accession,
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


if WEB_DIST.exists():
    app.mount("/", StaticFiles(directory=str(WEB_DIST), html=True), name="web")
