# Re-run The Server (Stale Container) And Show The Eval Set For Self-Check

- **Datetime:** 2026-06-26 07:26:45
- **Summary:** Confirm the public server is running (rebuild the stale container to current main), provide the tunnel URL, and display the accession-pinned eval set so the user can verify it themselves.

## Prompt

> is the server still running? run it if not, give me url, and show me the eval set we claim in this project, i want to check by myself /save-prompt

## What I Did

- **Server status:** the docker `app` + `cloudflared` were running, but the `app` image was ~27h
  old — it predated the round-1 / round-2 / README merges, so it was serving **stale code**.
  Rebuilt only the `app` service (`docker compose up -d --build app`) to reflect current main
  (`9f8edf3`), which **preserved the Cloudflare quick-tunnel URL** (only `app` recreated, not
  `cloudflared`). Confirmed healthy; local and public `/health` both 200; `/api/demo` and the open
  `apple` demo both 200.
- **Public URL:** `https://REDACTED.trycloudflare.com` (ephemeral quick
  tunnel — rotates only if `cloudflared` restarts). Access token for the free-form/upload endpoints
  (`SEC10K_ACCESS_TOKEN`, from gitignored `.env`) provided to the user; curated demos are open
  (no token).
- **Eval set shown for self-check:** displayed all **21 accession-pinned, immutable filings** from
  `eval/eval_set.json` (id / accession / sector / structure / RED) — 6 tracked RED failures
  (bac-fy2023, scwo-fy2025-amend, wmt-fy2003, amt-fy1997, ms-fy2024, hon-fy2024), every one flagged,
  silent-failure 0.
- Saved this prompt (Taipei time). No code changed; nothing pushed.
