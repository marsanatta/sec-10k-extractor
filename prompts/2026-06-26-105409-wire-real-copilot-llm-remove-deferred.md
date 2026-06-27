# Wire A Real LLM (GitHub Copilot SDK), Remove The Deferred Stub, Update The Docs

- **Datetime:** 2026-06-26 10:54:09
- **Summary:** Replace the deferred-stub LLM tier with a real GitHub Copilot SDK client (per browser-agent), update ANALYSIS/README/others; or justify why not — the user leans "why not try it?"

## Prompt

> another thing, I want you to remove the deferred LLM and update this repo corresponding analysis md files and others (scan it and update) we should use real LLM not fake it, it is pointless to me. see pj browser-agent how to use copilot sdk for real LLM calling unless you have strong justification you can discuss with me why not, or i mean why not try it? /save-prompt

## What I Did

- **Did NOT refuse** — assessed honestly that there is no strong justification against it, and that a
  real (constrained) LLM is actually MORE rubric-aligned: it makes the already-built apply-loop +
  token ledger fire for real, and turns the §3 cost story from a projection into a MEASURED number,
  without breaking "index, don't generate" (the LIB prompt still forces a closed-set line-ref, and
  the answer is verified + applied with structural re-validation; bad answers rejected).
- **Grounded the Copilot SDK pattern from browser-agent** (`backend/app/agent/models.py`):
  `github-copilot-sdk==1.0.2`, stdio mode `CopilotClient()` + `await client.start()` auto-auths from
  `COPILOT_GITHUB_TOKEN`/`GH_TOKEN`/`GITHUB_TOKEN` (no separate server needed), async, token usage
  from the `assistant.usage` event, mock fallback when the package/token is absent. Our Dockerfile is
  already glibc (python:3.11-slim) for the manylinux wheel.
- **Proposed plan:** a `CopilotLLMClient` (async-wrapped, implements the existing `LLMClient`
  Protocol's `adjudicate -> Adjudication`); `pipeline.py` default = real client when a token is
  present, else graceful fallback to `DeferredLLMClient`; add `github-copilot-sdk` as an optional dep;
  docker-compose passes `GH_TOKEN` like browser-agent; a token-backed measurement run on a few flagged
  filings for REAL cost; scan + rewrite ANALYSIS §3/§7, README, escalation docstrings; keep the
  offline suite network-free (CI uses the mock, never the real Copilot).
- **Surfaced two decisions for the user** before executing: (1) graceful-fallback "real-when-
  configured" (recommended — keeps offline CI network-free + a token-less deploy working + lets us
  measure real cost) vs hard-replace the stub; (2) whether `gh auth token` on this machine has Copilot
  Requests permission so I can MEASURE real cost, else wire+mock and leave the real measurement to the
  user. Will execute in a separate worktree after the running structural sweep lands + the user's go.
  Saved this prompt (Taipei time). No code changed yet.
