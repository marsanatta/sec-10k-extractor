from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Protocol

from sec10k.items import CANONICAL_BY_KEY
from sec10k.schema import Band, ExtractionResult, Status

_TOKEN_VARS = ("COPILOT_GITHUB_TOKEN", "GH_TOKEN", "GITHUB_TOKEN")
# Default OFF. The deterministic regex path is the shipped, $0, reproducible primary; the LLM tier
# is an explicit operator opt-in. Measured (research/llm-measurement-findings.md): no independent-
# signal gain on our gold, so it stays an available graceful-fallback, never on by default.
_ENABLE_VAR = "SEC10K_LLM_ESCALATION"


def llm_escalation_enabled() -> bool:
    return os.environ.get(_ENABLE_VAR, "").strip().lower() in ("1", "true", "yes", "on")


@dataclass(frozen=True)
class Adjudication:
    """A boundary-adjudication response together with the token cost of producing it. Real
    providers report usage on every call; the per-filing ledger sums these so escalation cost
    is measured, not estimated."""

    text: str
    input_tokens: int = 0
    output_tokens: int = 0


class LLMClient(Protocol):
    name: str

    def adjudicate(self, prompt: str) -> Adjudication | None:
        """Return the model's boundary-adjudication response with its token usage, or None if
        no call was made."""


class DeferredLLMClient:
    """The graceful-fallback / recording-only provider. Makes no call: escalation triggers still
    fire and are recorded, so the pipeline is fully functional (and the offline suite stays
    network-free) when no Copilot token is configured."""

    name = "deferred"

    def adjudicate(self, prompt: str) -> Adjudication | None:
        return None


def default_llm_client(model: str | None = None) -> LLMClient:
    """Pick the escalation provider: the REAL GitHub Copilot client when a token is configured in
    the environment, else the deferred (recording-only) stub. This is the graceful-fallback
    "real-when-configured" contract -- a token-less environment (CI, or a deploy without a Copilot
    PAT) gets the stub, so the tier degrades cleanly and the offline suite never makes a network
    call. Import is lazy so the SDK is only required when a token is actually present. `model`
    selects the Copilot model (UI-configurable); None falls back to the configured default.

    DEFAULT OFF: the real client is used only when the operator explicitly enables the tier
    (`SEC10K_LLM_ESCALATION`) AND a token is present. Token presence alone does NOT turn it on, so
    the default extract path stays deterministic ($0) even on a token-configured server."""
    if llm_escalation_enabled() and any(os.environ.get(v) for v in _TOKEN_VARS):
        try:
            from sec10k.copilot_client import CopilotLLMClient

            return CopilotLLMClient(model=model)
        except Exception:
            return DeferredLLMClient()
    return DeferredLLMClient()


def escalation_candidates(result: ExtractionResult) -> list[str]:
    """Item keys whose boundary is uncertain enough to warrant LLM adjudication: any
    present item not at HIGH confidence, plus expected items we failed to find."""
    out = []
    for it in result.items:
        if it.status == Status.PRESENT and it.confidence.band != Band.HIGH:
            out.append(it.item)
        elif it.status == Status.EXTRACTION_FAILURE:
            out.append(it.item)
    return out


def build_lib_prompt(canonical: str, item_key: str, char_start: int, window: int = 2000) -> str:
    """Build an 'index-don't-generate' (LIB) prompt: the model is shown numbered lines
    around a candidate boundary and must return the line number where the item begins. It
    indexes into the source; it never authors text. The response is constrained downstream
    to a closed item set + an in-range line id."""
    title = CANONICAL_BY_KEY[item_key].title
    lo = max(0, char_start - window)
    hi = min(len(canonical), char_start + window)
    numbered = "\n".join(f"{i}: {ln}" for i, ln in enumerate(canonical[lo:hi].splitlines()))
    return (
        f"You are locating the start of SEC 10-K Item {item_key} ({title}).\n"
        f"Return ONLY the integer line number where Item {item_key} begins, chosen from the "
        f"numbered lines below. Do not write any prose.\n\n{numbered}"
    )


def _line_ref_to_offset(
    canonical: str, char_start: int, line_text: str, window: int = 2000
) -> int | None:
    """Map an LLM line-number answer (from the numbered window of build_lib_prompt) back to an
    absolute char offset in the canonical. Returns None if the answer is not a valid in-range
    line number, so a malformed or out-of-range response is rejected and never applied. The
    window math mirrors build_lib_prompt exactly (same lo/hi), so line index N maps to the start
    of the N-th window line."""
    try:
        line_no = int(str(line_text).strip())
    except (ValueError, TypeError):
        return None
    lo = max(0, char_start - window)
    hi = min(len(canonical), char_start + window)
    lines = canonical[lo:hi].splitlines(keepends=True)
    if not (0 <= line_no < len(lines)):
        return None
    return lo + sum(len(lines[i]) for i in range(line_no))


def run_escalation(
    result: ExtractionResult, canonical: str, client: LLMClient | None, model: str | None = None
) -> dict:
    """Identify escalation candidates and, when a real client is wired, adjudicate each present
    low-confidence boundary, sum the real token cost, AND apply the model's line answer to move
    the item's char_range to the corrected start. With the deferred stub the triggers fire but no
    call is made (calls/tokens/applied stay 0); every candidate is annotated so nothing is
    silently skipped."""
    candidates = escalation_candidates(result)
    client = client or default_llm_client(model)
    deferred = getattr(client, "name", "") == "deferred"
    note = "escalation_deferred" if deferred else "escalated"
    by_key = {it.item: it for it in result.items}
    calls = input_tokens = output_tokens = applied = 0
    moved: list[str] = []
    for key in candidates:
        it = by_key.get(key)
        if it is None:
            continue
        if note not in it.provenance.checks_failed:
            it.provenance.checks_failed.append(note)
        if deferred or not it.char_range:
            continue
        adj = client.adjudicate(build_lib_prompt(canonical, key, it.char_range[0]))
        if adj is None:
            continue
        calls += 1
        input_tokens += adj.input_tokens
        output_tokens += adj.output_tokens
        new_start = _line_ref_to_offset(canonical, it.char_range[0], adj.text)
        # Apply only a valid, span-preserving correction (in range, non-empty, actually moves);
        # a malformed / out-of-range / no-op answer is rejected so the boundary never degrades.
        if new_start is not None and new_start != it.char_range[0] and 0 <= new_start < it.char_range[1]:
            it.char_range = (new_start, it.char_range[1])
            it.text = canonical[new_start:it.char_range[1]]
            if "escalation_applied" not in it.provenance.checks_passed:
                it.provenance.checks_passed.append("escalation_applied")
            applied += 1
            moved.append(key)
    return {
        "escalation_candidates": candidates,
        "escalation_provider": getattr(client, "name", "unknown"),
        "escalation_performed": not deferred,
        "escalation_calls": calls,
        "escalation_input_tokens": input_tokens,
        "escalation_output_tokens": output_tokens,
        "escalation_applied": applied,
        "escalation_items_moved": moved,
        # Observability for the failure census: did a REAL escalation call actually fire on this
        # filing (deferred/no-candidate filings stay False), so llm-touched records are separable.
        "llm_touched": calls > 0,
    }
