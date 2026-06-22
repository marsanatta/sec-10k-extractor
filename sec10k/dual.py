from __future__ import annotations

from sec10k.items import CANONICAL_BY_KEY


def title_matches(
    canonical: str, spans: dict[str, tuple[int, int]], window: int = 300
) -> dict[str, bool]:
    """Independent (title-anchored) cross-check. For each segmented item, does the item's
    own canonical TITLE appear at the start of its span? The segmenter anchors on the
    "Item N" NUMBER; this checks the TITLE text instead, so a mislabelled span (number
    says Item 7 but the prose is Item 8's) fails the check. A genuinely different signal
    from the number anchor, so it is not self-consistency.

    Returns True/False per present item. `[Reserved]` items have no title text and are
    reported True (not penalised)."""
    low = canonical.lower()
    out: dict[str, bool] = {}
    for key, (start, _end) in spans.items():
        title = CANONICAL_BY_KEY[key].title.lower()
        if title.startswith("["):
            out[key] = True
            continue
        out[key] = title[:20] in low[start : start + window]
    return out
