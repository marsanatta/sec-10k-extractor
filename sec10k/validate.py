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

# A real 10-K body (first item to end) covers most of the document. Coverage far below
# this means the chosen spans are not the body (e.g. the segmenter latched onto the table
# of contents). This is the non-tautological mis-segmentation detector: unlike the tiling
# invariants below, it is NOT guaranteed by the segmenter's construction.
MIN_COVERAGE = 0.4


def structural_invariants(ranges: list[tuple[int, int]]) -> dict[str, bool]:
    """Tiling invariants. NOTE: the current segmenter emits a contiguous, ordered,
    non-overlapping tiling by construction, so these pass on its output by design. They
    are kept as cheap regression guards for any extractor (P2 SGML, future LLM spans) that
    might NOT tile -- they are not, on their own, evidence the segmentation is correct."""
    pairs = list(zip(ranges, ranges[1:]))
    return {
        "monotonic": all(a[0] < b[0] for a, b in pairs),
        "non_overlapping": all(a[1] <= b[0] for a, b in pairs),
        "contiguous": all(a[1] == b[0] for a, b in pairs),
    }


def round_trip(ranges: list[tuple[int, int]], canonical: str) -> tuple[bool, float]:
    """Reconstruct the document as preamble + concatenated item spans; it must equal the
    canonical text byte-for-byte. Proves coverage has no dropped/duplicated text (again
    guaranteed by the current tiling segmenter; a real guard for non-tiling extractors)."""
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


def _band_present(global_ok: bool, content: bool, title_match: bool) -> Band:
    # A filing-level structural / coverage break makes every present item suspect.
    if not global_ok:
        return Band.LOW
    # HIGH needs BOTH independent per-item signals (keyword content AND title-at-start);
    # missing either is only MEDIUM, never HIGH -- absence of corroboration is not trust.
    if content and title_match:
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
    title_match: dict[str, bool],
) -> tuple[list[Item], dict]:
    """Run the validation stack, attach per-item confidence + provenance, classify absent
    items, and return (all_items_in_canonical_order, filing_summary)."""
    ranges = [it.char_range for it in present_items if it.char_range]
    struct = structural_invariants(ranges)
    rt_ok, rt_frac = round_trip(ranges, canonical)
    coverage_plausible = rt_frac >= MIN_COVERAGE
    global_ok = all(struct.values()) and rt_ok and coverage_plausible
    global_checks = {**struct, "round_trip": rt_ok, "coverage_plausible": coverage_plausible}

    for it in present_items:
        cok = content_ok(it.item, it.text)
        tmatch = title_match.get(it.item, False)
        band = _band_present(global_ok, cok, tmatch)
        passed = [k for k, v in global_checks.items() if v]
        failed = [k for k, v in global_checks.items() if not v]
        (passed if cok else failed).append("content")
        (passed if tmatch else failed).append("title_match")
        it.confidence = Confidence(band=band, score=_SCORE[band], signals=passed)
        it.provenance = Provenance(
            extractors=["anchor", "title"], checks_passed=passed, checks_failed=failed
        )

    present_keys = {it.item for it in present_items}
    absent = _classify_absent(present_keys, profile)
    all_items = sorted(present_items + absent, key=lambda it: CANONICAL_ORDER[it.item])

    n_fail = sum(1 for it in absent if it.status == Status.EXTRACTION_FAILURE)
    n_low = sum(1 for it in present_items if it.confidence.band == Band.LOW)
    n_med = sum(1 for it in present_items if it.confidence.band == Band.MEDIUM)
    title_mismatches = sum(1 for it in present_items if not title_match.get(it.item, False))

    # needs_review is an OR of genuinely independent problem signals (each reachable on its
    # own), NOT a restatement of the tiling invariant. The eval harness (P4) measures the
    # silent-failure RATE: filings that are NOT needs_review but disagree with gold.
    needs_review = (
        not all(struct.values())
        or not rt_ok
        or not coverage_plausible
        or n_fail > 0
        or n_low > 0
    )
    summary = {
        "items_present": len(present_items),
        "items_legitimately_absent": sum(
            1 for it in absent if it.status == Status.LEGITIMATELY_ABSENT
        ),
        "items_extraction_failure": n_fail,
        "structural_ok": all(struct.values()),
        "round_trip_ok": rt_ok,
        "coverage_fraction": round(rt_frac, 4),
        "coverage_plausible": coverage_plausible,
        "title_mismatches": title_mismatches,
        "low_confidence_items": n_low,
        "medium_confidence_items": n_med,
        "needs_review": needs_review,
    }
    return all_items, summary
