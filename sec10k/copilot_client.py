"""Real LLM escalation provider over the GitHub Copilot SDK.

Implements the `LLMClient` protocol (`adjudicate`) so the escalation tier can make a *real*
boundary-adjudication call instead of the deferred stub. It stays inside the "index, don't
generate" contract: the prompt is the closed-set, line-ref-only LIB prompt (`build_lib_prompt`),
and the answer is parsed back to a char offset + applied with structural re-validation by
`run_escalation`; a malformed/empty/failed call returns None so nothing degrades.

Auth/transport mirror browser-agent: stdio against the bundled `copilot` CLI, which auto-auths
from COPILOT_GITHUB_TOKEN / GH_TOKEN / GITHUB_TOKEN. The SDK is ASYNC; we keep one event loop +
one Copilot client alive on a background thread for the life of this instance (one CLI startup per
filing, reused across that filing's candidates) and expose a SYNC `adjudicate` via
`run_coroutine_threadsafe`. Token usage is read from the `assistant.usage` event so the per-filing
ledger records REAL input/output tokens.

This module is imported only when a token is configured (see `escalation.default_llm_client`); the
offline test suite never touches it.
"""
from __future__ import annotations

import asyncio
import os
import threading

from sec10k.escalation import Adjudication

_DEFAULT_MODEL = "gpt-5.4-mini"  # small/fast, fine for "return one line number"; override w/ COPILOT_MODEL


class CopilotLLMClient:
    name = "copilot"

    def __init__(self, model: str | None = None, timeout: int = 120) -> None:
        self.name = f"copilot:{model or os.environ.get('COPILOT_MODEL', _DEFAULT_MODEL)}"
        self._model = model or os.environ.get("COPILOT_MODEL", _DEFAULT_MODEL)
        self._timeout = timeout
        self._loop: asyncio.AbstractEventLoop | None = None
        self._client = None  # copilot.CopilotClient, lazily started
        self._lock = threading.Lock()

    def _ensure_loop(self) -> asyncio.AbstractEventLoop:
        if self._loop is None:
            self._loop = asyncio.new_event_loop()
            threading.Thread(target=self._loop.run_forever, daemon=True).start()
        return self._loop

    async def _adjudicate(self, prompt: str) -> Adjudication:
        from copilot import CopilotClient
        from copilot.session import PermissionHandler

        if self._client is None:
            self._client = CopilotClient()  # stdio; auto-auths from the env token
            await self._client.start()

        usage: dict[str, int] = {}

        def _on_event(event) -> None:
            data = getattr(event, "data", None)
            if data is not None:
                for k in ("input_tokens", "output_tokens"):
                    v = getattr(data, k, None)
                    if isinstance(v, int):
                        usage[k] = usage.get(k, 0) + v

        session = await self._client.create_session(
            on_permission_request=PermissionHandler.approve_all, model=self._model
        )
        try:
            session.on(_on_event)
        except Exception:
            pass
        resp = await session.send_and_wait(prompt)
        data = getattr(resp, "data", None) or resp
        content = getattr(data, "content", None) or ""
        out = usage.get("output_tokens") or (getattr(data, "output_tokens", 0) or 0)
        return Adjudication(text=str(content).strip(),
                            input_tokens=usage.get("input_tokens", 0),
                            output_tokens=int(out))

    def adjudicate(self, prompt: str) -> Adjudication | None:
        """Sync entry point for run_escalation. Returns None on ANY auth/SDK/timeout error, so a
        wired-but-failing provider degrades to the recording-only path instead of crashing."""
        try:
            with self._lock:  # the CLI session is not concurrency-safe; serialize per instance
                fut = asyncio.run_coroutine_threadsafe(self._adjudicate(prompt), self._ensure_loop())
                return fut.result(timeout=self._timeout)
        except Exception:
            return None
