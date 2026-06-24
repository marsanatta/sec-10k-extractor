# eng-pipe The Dockerize Plan + Verify Assignment Functions In Real Docker

- **Datetime:** 2026-06-23 22:08:04 (Asia/Taipei, UTC+8)
- **Summary:** Run /eng-pipe on the previously-planned dockerize work, but with the eng-test stage actually starting the server in Docker (`docker compose up`) and exercising the ASSIGNMENT.md functions through the running container / public tunnel to confirm they work. Use /eng-debug to RCA any failure and fix until pass. Then commit and /save-prompt.

## Prompt

> commit and you can start /eng-pipe for the dockerize plan in the eng-test. i want you to really start the server in docker and test the functions in assignment.md make sure they working. for any bug use /eng-debug to find RCA and fix until pass /save-prompt

## What I Did

- **Committed pending** prompt records (`2293686`) before starting.
- **Code (eng-pipe):** implemented the dockerize plan, updated for the security gate already in place:
  - `docker-compose.yml` (new) — `app` (build ., `env_file .env`, `8000:8000`, healthcheck on `/health`) + `cloudflared` (zero-config quick tunnel `--url http://app:8000`, depends_on app healthy; named-tunnel upgrade documented).
  - `api/server.py` — `GET /health` (ungated, before the SPA mount) for the healthcheck.
  - `.env.example` — added optional `CLOUDFLARE_TUNNEL_TOKEN` + reserved future `GH_TOKEN`.
  - `web/README.md` — `docker compose` + public-URL + token instructions; host-port-remap and ~100s tunnel-timeout notes.
  - `api/test_api.py` — `/health` unit test (12 api tests pass).
- **Real Docker eng-test:** `docker compose build` (image built clean — edgartools 5.39.1 installs fine on `python:3.11-slim`), `docker compose up -d` (app **healthy**, cloudflared quick tunnel up). Public URL `https://<random>.trycloudflare.com`. Through the public tunnel, every ASSIGNMENT.md function verified: `/health` 200, SPA served, `/api/demo` (5 demos), `/api/eval` 200, gate (`/api/extract` 401 without token), and `/api/extract` with the token on a still-hard filing (M2i: 23 items, 12 `extraction_failure`, `needs_review`) and a clean one (KO: 23 present, 0 failures, high-confidence items 1/1A/1B/1C/2/4/5/6/7A/8/9/9A).
- **eng-debug (RCA):** host `localhost:8000` initially 404'd with `{"error":"not found"}` while the container healthcheck passed. Traced: `Get-NetTCPConnection` showed an unrelated **`node` process bound to `127.0.0.1:8000`** shadowing Docker's published port for IPv4 localhost; the container's own logs showed only internal healthchecks (host curls never reached it). NOT our bug. Proved it by (a) testing through the tunnel (cloudflared -> app over the Docker network, unaffected) and (b) running the image on a free host port (`18000` -> 200). Documented the remap in the README.
- **Cleanup + commit:** `docker compose down`, removed the local test `.env` (gitignored; user creates their own via README). Committed `c0ed849` (no secrets in diff, neutral author). Did NOT push.

## Note
The compose passes both `SEC_EDGAR_USER_AGENT` and `SEC10K_ACCESS_TOKEN` from the git-ignored `.env`; reviewers reach the public tunnel URL and supply the token in the UI (stored in localStorage). Still pending for the full assignment: root README + analysis report, and an actual long-lived public deployment (the quick-tunnel URL is per-session).
