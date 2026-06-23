# Web frontend — SEC 10-K Item Extractor

FastAPI backend (`api/`) + React + Vite + TypeScript SPA (`web/`). The SPA lets a reviewer
submit or pick a filing, inspect every canonical Item 1–16 with its source-boundary
highlight, and read calibrated confidence + provenance. Honest about failures: GE is shown
mis-segmented (items cover ~1% of the document), M2i has its unlocated items flagged as
extraction failures, and the LLM escalation tier is a deferred stub (it did not run).

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

## Prod + public URL (`docker compose`)

`docker compose` runs two services: `app` (the container above — builds the SPA and serves it
from FastAPI alongside `/api/*`) and `cloudflared`, which opens a **Cloudflare quick tunnel**
and prints a public `https://<random>.trycloudflare.com` URL — no Cloudflare account needed.

```bash
cp .env.example .env          # then edit: set SEC_EDGAR_USER_AGENT and SEC10K_ACCESS_TOKEN
docker compose up --build -d
docker compose logs cloudflared | grep trycloudflare.com   # <- your public URL
```

- `SEC_EDGAR_USER_AGENT` — required, or `/api/extract` returns 500.
- `SEC10K_ACCESS_TOKEN` — required before exposing the tunnel: it gates `POST /api/extract`
  (503 if unset, 401 if wrong). Share it with reviewers out-of-band; the UI prompts for it and
  stores it in `localStorage`. `/health`, `/api/demo`, `/api/eval` and the SPA stay open.

For a **stable** URL instead of the rotating quick-tunnel one, create a named tunnel in the
Cloudflare Zero Trust dashboard, set `CLOUDFLARE_TUNNEL_TOKEN` in `.env`, and swap the
`cloudflared` command (see the comment in `docker-compose.yml`).

> Note: a Cloudflare quick tunnel has a ~100s edge timeout. A cold fetch of a very large
> filing (e.g. GE, ~4MB) can approach that; retry — the result is then served from cache.
>
> Note: if host port 8000 is already taken, `docker compose up` still succeeds but
> `localhost:8000` reaches the other process — change the left side of the `ports` mapping in
> `docker-compose.yml` (e.g. `18000:8000`). The public tunnel URL is unaffected (cloudflared
> reaches the container over the Docker network, not the host port).

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
