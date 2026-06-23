# Implement A Token-Based Security Gate, Mirroring browser-agent

- **Datetime:** 2026-06-23 21:55:33 (Asia/Taipei, UTC+8)
- **Summary:** Study how pj browser-agent builds its token-based auth (read `backend/app/security.py` + the security design in `README.md` / `DESIGN.md`), verify the same approach is portable to sec-10k-extractor's FastAPI app, then implement it as a security gate on the public endpoint.

## Prompt

> refer to pj browser-agent how it build the token based auth and read the security design in its readme.md design.md, verify if you can implement the same way and implement it as security gate /save-prompt

## What I Did

- **Studied browser-agent's model** (`backend/app/security.py` + README "Public-tunnel access control"): a single shared secret `AGENT_ACCESS_TOKEN` gates the expensive public endpoints via Starlette `BaseHTTPMiddleware`. Constant-time compare (`secrets.compare_digest`); **fail-closed** (unset -> 503, wrong/absent -> 401); token from `Authorization: Bearer` (and an httponly cookie set at `POST /auth`, needed only so SSE/`<img>` — which can't set headers — can authenticate); **never** a `?token=` query param (leaks via logs/history/Referer); frontend prompts for it and stores it in `localStorage`. Threat model = protect the one operator's quota, not multi-tenant identity (no per-user revocation/audit — explicitly out of scope).
- **Verified portable — yes.** Same FastAPI/Starlette stack; analogous threat (public tunnel URL lets anyone hammer `/api/extract`, each call a slow live EDGAR fetch -> burns our rate-limit budget + ties up the worker pool). One justified simplification: we have **no SSE**, so the SPA `fetch` sets headers directly — dropped the cookie + `POST /auth` exchange, kept the Bearer-header path.
- **Implemented:**
  - `api/security.py` (new) — `TokenAuthMiddleware`, `SEC10K_ACCESS_TOKEN`, protects prefix `/api/extract`, constant-time compare, 503/401, Bearer only.
  - `api/server.py` — `app.add_middleware(TokenAuthMiddleware)`.
  - Frontend — `api.ts` `extract(req, token)` sends `Authorization: Bearer`; `App.tsx` token state backed by `localStorage`; `InputBar.tsx` adds a password "Access token" field.
  - `.env.example` — `SEC10K_ACCESS_TOKEN` with generation hint; `.gitignore` — ignore `.claude/worktrees/`.
  - `api/test_api.py` — updated existing extract tests (gate runs first, so they set the token + send the header) + 3 new gate tests (503 unconfigured / 401 wrong / 401 absent).
- **Verified (traced, not assumed):** `python -m pytest -q` -> **49 passed**; `npm run build` clean; `npm test` -> 15 passed. **Live trace through uvicorn:** no token configured -> `/api/extract` 503; token set -> `/api/demo` (open) 200, no-auth 401, wrong-token 401, correct-token 200 with a real M2i extraction.
- Committed (`c44f6a9`, neutral author, no AI attribution). No secrets/PII in the diff. Did NOT push.

## Note
`/api/demo` also routes extraction through `/api/extract`, so reviewers need the shared token even for demo picks (consistent with browser-agent's "share the token with evaluators out-of-band"). Open question for later: whether to pre-warm + serve demo results through an ungated path so casual viewers can browse without a token.
