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
    most important thing the eval set exists to detect. Should be ~0; any hit is a hole."""
    if result.summary.get("needs_review"):
        return False
    return presence_scores(result, expected_present)["recall"] < 1.0


def fmt_rate(k: int, n: int) -> str:
    if n == 0:
        return "0/0 (n/a)"
    center, half = wilson_ci(k, n)
    lo, hi = max(0.0, center - half), min(1.0, center + half)
    return f"{k}/{n} (obs {k / n:.2f}, 95% CI [{lo:.2f}, {hi:.2f}])"
