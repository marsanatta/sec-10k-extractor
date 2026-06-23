# Research + Plan: Dockerize With Cloudflare Tunnel And gh-Token LLM Readiness (Mirror browser-agent)

- **Datetime:** 2026-06-23 21:35:57 (Asia/Taipei, UTC+8)
- **Summary:** Research (no md artifact) how to dockerize sec-10k-extractor so it (1) runs the server in Docker and exposes a PUBLIC endpoint from this Windows desktop via Cloudflare Tunnel (cloudflared), like pj browser-agent, and (2) is ready to use a GitHub token (`gh auth token`) for a future LLM provider the same way browser-agent does. Then produce an implementation plan with /code-planner (no code yet — to review first).

## Prompt

> now /research [nomd] and see how to make this project dockeraize. you can refer to pj browser-agent. i want 1. be able to use cloudfront like browser agent to host the sever inside docker and expose public endpoint in this desktop 2. if we plan to use LLM in the pipeline in the future, mimic browser agent to use gh token. now plan for it with /code-planner

(Note: "cloudfront" was clarified to mean **Cloudflare Tunnel / `cloudflared`** — the desktop-exposes-public-endpoint pattern, not AWS CloudFront.)

## What I Did

- **Research ([nomd], inline):** read browser-agent's `Dockerfile`, `docker-compose.yml`, `.env.example`, and its own `prompts/2026-06-23-031113-dockerize-feasibility-copilot-sdk-and-tunnel.md` (it had already done this research). Findings:
  - **Public endpoint** = a second compose service `cloudflared` (`image: cloudflare/cloudflared`, default `command: tunnel --no-autoupdate --url http://app:<port>`) = a QUICK tunnel: no Cloudflare account, no token, prints an ephemeral `https://<random>.trycloudflare.com` (read from `docker compose logs cloudflared`). Named-tunnel upgrade = CF-issued `CLOUDFLARE_TUNNEL_TOKEN` in `.env` + command `tunnel run --token`.
  - **gh-token for LLM** = `.env` `GH_TOKEN=$(gh auth token)`; Copilot SDK auto-reads `GH_TOKEN`/`COPILOT_GITHUB_TOKEN`/`GITHUB_TOKEN`, no interactive login in-container. Needs a **glibc** base for the manylinux wheel (Alpine/musl unsupported).
  - **Key difference for us:** browser-agent needs a named tunnel only because its transport is SSE (quick tunnels don't support SSE). Our app is plain HTTP request/response → the **zero-config quick tunnel is sufficient** for the demo.
  - **Our repo is already favorable:** `Dockerfile` base is `python:3.11-slim` (glibc, satisfies the future Copilot wheel — no base change), uvicorn binds `0.0.0.0:8000` / `EXPOSE 8000` (tunnel-ready). Missing only: a `docker-compose.yml`, a `/health` endpoint for the healthcheck, and the extra `.env.example` keys.
- **Plan (via /code-planner, presented for review — NOT yet built):**
  1. New `docker-compose.yml`: `app` (build ., `env_file: .env`, `8000:8000`, restart, healthcheck on `/health`) + `cloudflared` (quick tunnel default `--url http://app:8000`, depends_on app healthy; named-tunnel upgrade documented).
  2. Add `GET /health` to `api/server.py` (3 lines, no env/network) BEFORE the StaticFiles mount — recommended over reusing `/api/demo` (conventional, decoupled).
  3. `.env.example`: keep `SEC_EDGAR_USER_AGENT`; add commented `CLOUDFLARE_TUNNEL_TOKEN` (optional named tunnel) and `GH_TOKEN` (future LLM tier).
  4. Future LLM tier: `sec10k/escalation.py` reads `GH_TOKEN`/`COPILOT_GITHUB_TOKEN` from env when implemented — reserve the env key now, do NOT wire it.
  5. Recommended NO app-level access-token gate (reviewers must operate it openly; abuse risk is low since it only fetches public SEC data) — defend rate-limit abuse at the platform layer (named tunnel + Cloudflare Access) if ever needed.
  6. **Flagged a real gotcha:** Cloudflare edge has a ~100s proxy timeout (Error 524); our `/api/extract` can reach ~120s on a cold GE (4MB) fetch → could be cut off through the tunnel. Mitigation: pre-warm the demo cache at startup so demo picks are instant; document that a cold huge filing may 524 on first fetch (retry hits cache). Number not yet live-verified against the tunnel.
- Did NOT write any code — plan is awaiting review.
