# Deploying to Zeabur (fixed public hostname)

This app runs as a **single persistent Docker container** (FastAPI serving the built React SPA).
Zeabur builds the repo's root `Dockerfile` and gives it a stable `https://<name>.zeabur.app` URL,
so **no Cloudflare tunnel is needed** — drop the `cloudflared` sidecar; Zeabur provides the public
ingress + TLS + a fixed hostname. Every function is identical to the local Docker run (EDGAR fetch,
the GitHub Copilot escalation tier via `GH_TOKEN`, the access-token gate, the 120 s extraction
timeout).

## What the platform builds

- Zeabur deploys the root **`Dockerfile`** (the `app` image), not `docker-compose.yml`. The
  `cloudflared` service in compose is local-only and is ignored.
- The container listens on **`$PORT`** if the platform injects one, else `8000`
  (`CMD … --port ${PORT:-8000}`).

## Environment variables (set in the Zeabur dashboard — never commit)

| Variable | Value | Purpose |
|---|---|---|
| `SEC_EDGAR_USER_AGENT` | `Your Name you@example.com` | SEC EDGAR fair-access requires a descriptive UA; the API returns 500 without it. |
| `SEC10K_ACCESS_TOKEN` | a long random secret | Gates `POST /api/extract` (the slow EDGAR-fetching path). Demos stay open. |
| `GH_TOKEN` | output of `gh auth token` (PAT with Copilot Requests) | Enables the REAL LLM escalation tier; absent ⇒ $0 deferred fallback. |
| `COPILOT_MODEL` *(optional)* | e.g. `claude-opus-4.8` | Server-side default escalation model. |

## Steps

1. Create a Zeabur account (sign in with GitHub).
2. New Project → **Deploy from GitHub** → pick `marsanatta/sec-10k-extractor`, branch `main`.
   Zeabur auto-detects the `Dockerfile`.
3. After the first build, open the service → **Variables** → add the env vars above → redeploy.
4. **Networking / Domains** → enable the free `*.zeabur.app` subdomain (the fixed hostname), or bind
   a custom domain.
5. Verify: `GET https://<name>.zeabur.app/health` → `{"status":"ok"}`; open `/` for the SPA; run a
   curated demo (open, no token); free-form extract needs the access token.

## Redeploys keep the same URL + reading logs (the two extra requirements)

- **Stable URL across deploys.** The `*.zeabur.app` subdomain (or a custom domain) is bound to the
  *service*, not to a build. Every `git push` triggers a new deployment **behind the same domain** —
  the public URL never changes (unlike the ephemeral `trycloudflare.com` tunnel, which rotated on
  every restart). That is the whole reason for moving off the tunnel.
- **Remote server logs — two ways:**
  - **Dashboard:** open the service → **Logs**. Runtime logs stream live; build logs are separate; a
    **Download** button exports a chosen time range.
  - **CLI:** `npm i -g zeabur` (or `npx zeabur@latest`), `zeabur auth login`, then stream the live
    runtime log: `zeabur deployment log -t runtime --service-name sec-10k-extractor`.

## Notes / caveats

- **Request timeout:** extractions can take up to 120 s. Confirm Zeabur's ingress timeout is ≥ that;
  the app already degrades gracefully (its own 120 s `EXTRACT_TIMEOUT_S` → 504 + a frontend error),
  same as the current Cloudflare quick tunnel (~100 s). Azure App Service (~230 s) is more generous
  if a longer hard ceiling is needed.
- **Outbound network:** the container must reach `sec.gov` (EDGAR) and the GitHub Copilot API — both
  are open egress on Zeabur.
- **Stateless restarts:** the in-memory result cache is rebuilt on restart (fine; filings are
  immutable and re-fetched on demand). No persistent volume required.
