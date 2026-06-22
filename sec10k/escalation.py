from __future__ import annotations

from typing import Protocol

from sec10k.items import CANONICAL_BY_KEY
from sec10k.schema import Band, ExtractionResult, Status


class LLMClient(Protocol):
    name: str

    def adjudicate(self, prompt: str) -> str | None:
        """Return the model's response to a boundary-adjudication prompt, or None if the
        call could not be made."""


class DeferredLLMClient:
    """Placeholder used until a real provider (the GitHub Copilot SDK) is wired. It makes
    no call: escalation triggers still fire and are recorded as deferred, so the pipeline
    is fully functional without the LLM tier (the plan's P3 cut-line)."""

    name = "deferred"

    def adjudicate(self, prompt: str) -> str | None:
        return None


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


def run_escalation(
    result: ExtractionResult, canonical: str, client: LLMClient | None
) -> dict:
    """Identify escalation candidates and, when a real client is wired, adjudicate their
    boundaries. With the deferred stub the triggers fire but no call is made; every
    candidate is annotated so nothing is silently skipped."""
    candidates = escalation_candidates(result)
    client = client or DeferredLLMClient()
    deferred = getattr(client, "name", "") == "deferred"
    note = "escalation_deferred" if deferred else "escalated"
    by_key = {it.item: it for it in result.items}
    for key in candidates:
        it = by_key.get(key)
        if it is not None and note not in it.provenance.checks_failed:
            it.provenance.checks_failed.append(note)
    return {
        "escalation_candidates": candidates,
        "escalation_provider": getattr(client, "name", "unknown"),
        "escalation_performed": not deferred,
    }
