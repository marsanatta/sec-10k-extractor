"""Token gate for the publicly-exposed /api/extract endpoint.

Mirrors browser-agent/backend/app/security.py. Once the app is reachable over a public
URL, anyone who learns the URL could hammer /api/extract -- each call does a
slow live EDGAR fetch, so an open endpoint invites abuse of the author's SEC rate-limit
budget and ties up the worker pool. A single shared secret is the appropriate control for a
one-author demo (no per-user identity/revocation -- out of scope, same as browser-agent).

Fail-closed: if SEC10K_ACCESS_TOKEN is unset, the protected path returns 503 -- the author
must configure a token before exposing it publicly. Wrong/absent token -> 401.

The token is read from an `Authorization: Bearer` header only. We deliberately do NOT accept
a `?token=` query param: URL-borne tokens leak through access logs, proxy logs, browser
history, and Referer headers. (browser-agent additionally accepts an httponly cookie so its
SSE/<img> loads -- which cannot set headers -- can authenticate; we have no SSE, so the
header path alone suffices.)
"""

from __future__ import annotations

import os
import secrets

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

_PROTECTED_PREFIXES = ("/api/extract",)

# Reject oversized bodies from the Content-Length header BEFORE Starlette buffers them into
# memory (the per-endpoint char cap runs only after parsing, too late to stop an OOM). Sized
# to ~MAX_UPLOAD_CHARS * 4 bytes (worst-case UTF-8) for the paste/upload endpoint.
MAX_REQUEST_BYTES = 25_000_000


def _configured() -> str | None:
    return os.environ.get("SEC10K_ACCESS_TOKEN") or None


def _bearer(header: str | None) -> str | None:
    if header and header.lower().startswith("bearer "):
        return header[7:].strip()
    return None


def valid(supplied: str | None) -> bool:
    configured = _configured()
    if not configured or not supplied:
        return False
    return secrets.compare_digest(supplied, configured)


class TokenAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        length = request.headers.get("content-length")
        if length and length.isdigit() and int(length) > MAX_REQUEST_BYTES:
            return JSONResponse({"error": "Request body too large."}, status_code=413)
        if any(request.url.path.startswith(p) for p in _PROTECTED_PREFIXES):
            if _configured() is None:
                return JSONResponse(
                    {"error": "SEC10K_ACCESS_TOKEN is not configured on the server."},
                    status_code=503,
                )
            if not valid(_bearer(request.headers.get("authorization"))):
                return JSONResponse(
                    {"error": "Unauthorized -- provide the access token shared by the author."},
                    status_code=401,
                )
        return await call_next(request)
