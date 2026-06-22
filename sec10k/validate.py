from __future__ import annotations

from sec10k.items import CANONICAL_ITEMS, CANONICAL_ORDER
from sec10k.schema import Band, Confidence, Item, Provenance, Status
from sec10k.template import EXPECTED, FilerProfile, expectation

# Signature words an item's text should contain — a weak, cheap sanity signal.
_KEYWORDS = {
    "1": ("business",),
    "1A": ("risk",),
    "2": ("propert",),
    "3": ("legal", "proceeding"),
    "7": ("operation", "discussion", "results"),
    "8": ("financial",),
    "9A": ("control", "procedure"),
}

_SCORE = {Band.HIGH: 0.9, Band.MEDIUM: 0.6, Band.LOW: 0.3, Band.UNSCORED: None}


def structural_invariants(ranges: list[tuple[int, int]]) -> dict[str, bool]:
    pairs = list(zip(ranges, ranges[1:]))
    return {
        "monotonic": all(a[0] < b[0] for a, b in pairs),
        "non_overlapping": all(a[1] <= b[0] for a, b in pairs),
        "contiguous": all(a[1] == b[0] for a, b in pairs),
    }


def round_trip(ranges: list[tuple[int, int]], canonical: str) -> tuple[bool, float]:
    """Reconstruct the document as preamble + concatenated item spans; it must equal the
    canonical text byte-for-byte. Proves coverage (no dropped/duplicated text); it does
    not prove the labels are correct, so it is paired with the other signals."""
    if not ranges or not canonical:
        return False, 0.0
    ordered = sorted(ranges)
    reconstructed = canonical[: ordered[0][0]] + "".join(canonical[s:e] for s, e in ordered)
    frac = sum(e - s for s, e in ordered) / len(canonical)
    return reconstructed == canonical, frac


def content_ok(item_key: str, text: str) -> bool:
    kws = _KEYWORDS.get(item_key)
    if not kws:
        return True
    low = text.lower()
    return any(k in low for k in kws)


def _band_present(global_ok: bool, content: bool, agree) -> Band:
    if not global_ok:
        return Band.LOW
    if content and agree is not False:
        return Band.HIGH
    return Band.MEDIUM


def _classify_absent(present_keys: set[str], profile: FilerProfile) -> list[Item]:
    out = []
    for ci in CANONICAL_ITEMS:
        if ci.key in present_keys:
            continue
        exp = expectation(ci.key, profile)
        if exp == EXPECTED:
            status, band, note = Status.EXTRACTION_FAILURE, Band.LOW, "expected_but_not_found"
        else:
            status, band, note = Status.LEGITIMATELY_ABSENT, Band.HIGH, f"template:{exp}"
        out.append(
            Item(
                item_id=ci.item_id, part=ci.part, item=ci.key, title=ci.title,
                text="", char_range=None, status=status,
                confidence=Confidence(band=band, score=_SCORE[band], signals=[note]),
                provenance=Provenance(
                    extractors=["template"],
                    checks_failed=[note] if status == Status.EXTRACTION_FAILURE else [],
                ),
            )
        )
    return out


def assess(
    present_items: list[Item],
    canonical: str,
    profile: FilerProfile,
    agree_map: dict[str, bool],
) -> tuple[list[Item], dict]:
    """Run the validation stack, attach per-item confidence + provenance, classify absent
    items, and return (all_items_in_canonical_order, filing_summary)."""
    ranges = [it.char_range for it in present_items if it.char_range]
    struct = structural_invariants(ranges)
    rt_ok, rt_frac = round_trip(ranges, canonical)
    global_ok = all(struct.values()) and rt_ok
    global_checks = {**struct, "round_trip": rt_ok}

    for it in present_items:
        cok = content_ok(it.item, it.text)
        agree = agree_map.get(it.item)
        band = _band_present(global_ok, cok, agree)
        passed = [k for k, v in global_checks.items() if v]
        failed = [k for k, v in global_checks.items() if not v]
        (passed if cok else failed).append("content")
        if agree is True:
            passed.append("dual_agreement")
        elif agree is False:
            failed.append("dual_agreement")
        it.confidence = Confidence(band=band, score=_SCORE[band], signals=passed)
        it.provenance = Provenance(
            extractors=["anchor", "title"], checks_passed=passed, checks_failed=failed
        )

    present_keys = {it.item for it in present_items}
    absent = _classify_absent(present_keys, profile)
    all_items = sorted(present_items + absent, key=lambda it: CANONICAL_ORDER[it.item])

    n_fail = sum(1 for it in absent if it.status == Status.EXTRACTION_FAILURE)
    n_low = sum(1 for it in present_items if it.confidence.band == Band.LOW)
    summary = {
        "items_present": len(present_items),
        "items_legitimately_absent": sum(
            1 for it in absent if it.status == Status.LEGITIMATELY_ABSENT
        ),
        "items_extraction_failure": n_fail,
        "structural_ok": all(struct.values()),
        "round_trip_ok": rt_ok,
        "coverage_fraction": round(rt_frac, 4),
        "low_confidence_items": n_low,
        # Silent failure = a coverage/structural break or a missing expected item that is
        # NOT surfaced by any flag. By construction each such case raises a flag above, so
        # this is 0 here; the eval harness (P4) measures the rate across many filings.
        "unflagged_failure": (not global_ok) and n_low == 0 and n_fail == 0,
    }
    return all_items, summary
