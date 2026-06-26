from __future__ import annotations

import math

from sec10k.schema import ExtractionResult, Status


def wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion. Returns (center, half_width).
    Used so every reported rate carries an honest error bar (small N -> wide bar)."""
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (center, half)


def present_keys(result: ExtractionResult) -> set[str]:
    return {it.item for it in result.items if it.status == Status.PRESENT}


def presence_scores(result: ExtractionResult, expected_present: list[str]) -> dict:
    """Item-presence precision/recall/F1 against a hand-labelled expected-present set.
    Recall is the load-bearing number (did we surface the items we KNOW are there); extra
    items beyond the conservative gold don't hurt recall, so precision is reported but not
    used for the silent-failure metric."""
    got = present_keys(result)
    exp = set(expected_present)
    tp = len(got & exp)
    prec = tp / len(got) if got else 0.0
    rec = tp / len(exp) if exp else 1.0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
    return {
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1": round(f1, 4),
        "missing": sorted(exp - got),
        "extra": sorted(got - exp),
    }


def label_free_signals(result: ExtractionResult) -> dict:
    s = result.summary
    item8_ok = s.get("item8_xbrl_found", 0) > 0 or s.get("item8_markers") is True
    return {
        "structural_ok": bool(s.get("structural_ok")),
        "round_trip_ok": bool(s.get("round_trip_ok")),
        "coverage_plausible": bool(s.get("coverage_plausible")),
        "item8_oracle_ok": bool(item8_ok),
        "needs_review": bool(s.get("needs_review")),
    }


def is_silent_failure(result: ExtractionResult, expected_present: list[str]) -> bool:
    """A silent failure: the system reports it does NOT need review, yet it missed an item
    the gold says should be present. That is a real error that raised no flag -- the single
    most important thing the eval set exists to detect. Should be ~0; any hit is a hole.

    Presence-level ONLY: this catches MISSING gold keys, not wrong boundaries on items that
    ARE present (char-exact boundary-drift detection needs char-labelled gold = STRETCH)."""
    if result.summary.get("needs_review"):
        return False
    return presence_scores(result, expected_present)["recall"] < 1.0


def _iou(a: tuple[int, int], b: tuple[int, int]) -> float:
    inter = max(0, min(a[1], b[1]) - max(a[0], b[0]))
    union = (a[1] - a[0]) + (b[1] - b[0]) - inter
    return inter / union if union > 0 else 0.0


def boundary_scores(result: ExtractionResult, gold_items: dict[str, list[int]], iou_thresh: float = 0.9) -> dict:
    """Char-exact boundary scoring against an audited gold (offsets per item). For each
    gold item, IoU of the extracted char_range vs the gold range; a match needs IoU >=
    threshold. This is the only signal that turns a WRONG boundary into a number rather than
    a needs_review flag -- the easy-filing spans are regex-derived but HUMAN-AUDITED, and m2i
    is method-independent of the regex/edgartools lineage, so it can catch the common-mode the
    cross-check is blind to."""
    ext = {it.item: it.char_range for it in result.items
           if it.status == Status.PRESENT and it.char_range}
    ious, matched = [], 0
    for k, g in gold_items.items():
        x = ext.get(k)
        iou = _iou(x, (g[0], g[1])) if x else 0.0
        ious.append(iou)
        if iou >= iou_thresh:
            matched += 1
    n = len(gold_items)
    return {
        "mean_iou": round(sum(ious) / n, 3) if n else None,
        "match_rate": round(matched / n, 3) if n else None,
        "matched": matched,
        "total": n,
    }


def fmt_rate(k: int, n: int) -> str:
    if n == 0:
        return "0/0 (n/a)"
    center, half = wilson_ci(k, n)
    lo, hi = max(0.0, center - half), min(1.0, center + half)
    return f"{k}/{n} (obs {k / n:.2f}, 95% CI [{lo:.2f}, {hi:.2f}])"


def scattered_item_check(result: ExtractionResult, item_key: str, tail_probe: str) -> dict:
    """A NON-CONTIGUOUS item (a bank's Item 7 MD&A spread across non-adjacent stretches) fails
    if the span stops at the first fragment. Given a probe known to belong to a LATE part of the
    item, report whether it falls INSIDE the extracted span. inside=False => the tail was dropped
    (a scattered-item failure, even though the item is 'present'). None => probe/item absent."""
    it = next((i for i in result.items if i.item == item_key and i.status == Status.PRESENT), None)
    if it is None or not it.char_range:
        return {"item": item_key, "present": False, "inside": None, "probe_pos": -1, "span": None}
    pos = result.canonical_text.find(tail_probe)
    s, e = it.char_range
    return {
        "item": item_key, "present": True, "probe_pos": pos, "span": [s, e],
        "inside": (s <= pos < e) if pos != -1 else None,
    }


# --- Signal D (round 2): classification-correctness vs a HUMAN-AUDITED per-form-type reference ---
# Production status -> {present, ok-absent, failure}; human gold label -> {present, ok-absent}.
# The gold uses the OBJECTIVE heading-exists rule: an item whose "Item X" heading physically exists
# in the filing body (substantive text OR "None."/"Not applicable" OR a "see proxy" incorporated-
# by-reference section the segmenter finds) is PRESENT; an item with NO heading at all (genuinely
# omitted, template-allowed) is LEGITIMATELY-ABSENT. There is deliberately NO separate
# "incorporated" category: a headed "incorporated by reference" item is present (production calls
# it present too -- the segmenter finds the heading), so giving it its own gold category would
# manufacture false present-vs-absent mismatches. "ok-absent" = the gold's legitimately-absent;
# "failure" is a production error (claimed-expected but not found). A match = production category
# == gold category. Decorrelated from needs_review: it compares production classification, item by
# item, to ground truth read from the filing -- not to any production flag.
_PROD_CAT = {
    Status.PRESENT: "present",
    Status.LEGITIMATELY_ABSENT: "ok-absent",
    Status.EXTRACTION_FAILURE: "failure",
}
_GOLD_CAT = {
    "present": "present",
    "legitimately-absent": "ok-absent",
}


def classification_match_rate(result: ExtractionResult, gold_labels: dict[str, str]) -> dict:
    """Signal D: fraction of items whose PRODUCTION status category matches the HUMAN-audited
    category in gold_labels (item_key -> present | legitimately-absent, per the heading-exists
    rule). The loop cannot move this by editing the classifier toward a target -- only by making
    classification match the independent reference. A gold 'ok-absent' (no heading) that production
    calls 'failure' (the form-blind bug) is a mismatch; a gold 'present' (heading exists) that
    production calls 'ok-absent' (an over-broad rule falsely excusing a headed item) is also a
    mismatch."""
    by_key = {it.item: it.status for it in result.items}
    matched, total, mismatches = 0, 0, []
    for k, label in gold_labels.items():
        gold = _GOLD_CAT.get(label)
        if gold is None:
            continue  # unknown/uninterpretable label is skipped, never silently counted as a match
        st = by_key.get(k)
        prod = _PROD_CAT.get(st, "failure") if st is not None else "failure"
        total += 1
        if prod == gold:
            matched += 1
        else:
            mismatches.append({"item": k, "gold": gold, "prod": prod})
    return {
        "match_rate": round(matched / total, 3) if total else None,
        "matched": matched,
        "total": total,
        "mismatches": mismatches,
    }
