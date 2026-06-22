from __future__ import annotations

from sec10k.items import CANONICAL_ITEMS


def title_boundaries(canonical: str, body_start: int) -> dict[str, int]:
    """Independent (title-anchored) segmentation: locate each canonical item by its TITLE
    text, scanning forward from the body start, rather than by its "Item N" number. This
    is a different signal from the number-anchored regex, so agreement between the two is
    a genuine cross-check (not self-consistency)."""
    low = canonical.lower()
    cur = max(body_start, 0)
    out: dict[str, int] = {}
    for ci in CANONICAL_ITEMS:
        title = ci.title.lower()
        if title.startswith("["):  # [Reserved] has no title text to anchor on
            continue
        needle = title[:25]
        idx = low.find(needle, cur)
        if idx != -1:
            out[ci.key] = idx
            cur = idx
    return out


def agreement(
    number_spans: dict[str, tuple[int, int]],
    title_starts: dict[str, int],
    tolerance: int = 400,
) -> dict[str, bool]:
    """Per item: do the number-anchored and title-anchored boundaries roughly coincide?
    The title normally sits just after the "Item N." header, so a small forward delta is
    expected; a missing title or a large delta is a disagreement worth flagging."""
    out: dict[str, bool] = {}
    for key, (start, end) in number_spans.items():
        t = title_starts.get(key)
        out[key] = t is not None and (start - tolerance) <= t <= end
    return out
