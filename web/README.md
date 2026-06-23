# Web frontend — SEC 10-K Item Extractor

FastAPI backend (`api/`) + React + Vite + TypeScript SPA (`web/`). The SPA lets a reviewer
submit or pick a filing, inspect every canonical Item 1–16 with its source-boundary
highlight, and read calibrated confidence + provenance. Honest about failures: GE is shown
mis-segmented, M2i as 0 items, and the LLM escalation tier as a deferred stub (it did not run).

## Prerequisites

- Python 3.11+, Node 20+
- An SEC EDGAR User-Agent. SEC fair-access requires `Name email`. Set it via env:
  ```
  cp .env.example .env   # then edit, or just export it
  export SEC_EDGAR_USER_AGENT="Your Name your@email.com"
  ```
  The API returns a clear `500 {error}` if it is unset; nothing is hardcoded.

## Dev (two processes, hot reload)

From the repo root:

```bash
pip install ".[api,dev]"
export SEC_EDGAR_USER_AGENT="Your Name your@email.com"
uvicorn api.server:app --reload --port 8000
```

In a second terminal:

```bash
cd web
npm install
npm run dev          # http://localhost:5173, proxies /api -> :8000
```

Open http://localhost:5173. Extraction is slow (10–60s; GE is ~4MB) — the UI shows a
spinner + elapsed seconds. Results are cached by accession server-side, so repeat views and
demo picks are instant.

## Prod (single container)

```bash
docker build -t sec10k-web .
docker run -p 8000:8000 -e SEC_EDGAR_USER_AGENT="Your Name your@email.com" sec10k-web
```

Open http://localhost:8000. The container builds the SPA, then serves it from FastAPI
(`StaticFiles` at `/`) alongside the JSON API at `/api/*`.

## Tests

```bash
# backend + existing pipeline tests
python -m pytest -q

# frontend pure-transform tests (status->color, confidence->label, group-by-part,
# slice-around-range edge cases)
cd web && npm run build && npm test
```

## API

- `POST /api/extract` `{ticker?, fiscal_year?, accession?}` → full `ExtractionResult` JSON
  including `canonical_text` (the source needed for the boundary highlight). Cached by
  accession.
- `GET /api/demo` → curated reviewer examples (Apple, KO, GE, M2i, MSFT-1995).
- `GET /api/eval` → `{markdown}` of `eval/report.md`.
- `GET /` → the built SPA.
