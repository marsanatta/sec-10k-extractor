from sec10k.evalkit import is_silent_failure, presence_scores, wilson_ci
from sec10k.schema import (
    Confidence,
    ExtractionResult,
    FilingMeta,
    Item,
    Provenance,
    Status,
)


def _result(present: list[str], needs_review: bool) -> ExtractionResult:
    items = [
        Item(
            item_id=f"I.{k}", part="I", item=k, title=k, text="t", char_range=(0, 1),
            status=Status.PRESENT, confidence=Confidence(), provenance=Provenance(),
        )
        for k in present
    ]
    meta = FilingMeta("", "", "", "10-K", "", None, "html", None, None)
    return ExtractionResult(meta, items, 1, {"needs_review": needs_review})


def test_wilson_ci():
    assert wilson_ci(0, 0) == (0.0, 0.0)
    c, h = wilson_ci(10, 10)
    assert c > 0.7 and h > 0          # all-success: center high, finite bar
    c2, h2 = wilson_ci(1, 4)
    assert 0 < c2 < 1 and h2 > 0.2    # small N -> wide bar


def test_presence_scores():
    r = _result(["1", "3"], needs_review=False)
    assert presence_scores(r, ["1", "3"])["recall"] == 1.0
    p = presence_scores(r, ["1", "3", "8"])
    assert p["recall"] < 1.0 and "8" in p["missing"]


def test_silent_failure_logic():
    clean = _result(["1", "3"], needs_review=False)
    assert is_silent_failure(clean, ["1", "3"]) is False          # recall 1.0 -> ok
    assert is_silent_failure(clean, ["1", "3", "8"]) is True       # missed 8, unflagged -> silent
    flagged = _result(["1", "3"], needs_review=True)
    assert is_silent_failure(flagged, ["1", "3", "8"]) is False    # missed but flagged -> not silent
