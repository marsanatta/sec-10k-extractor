from sec10k.evalkit import boundary_scores, is_silent_failure, presence_scores, wilson_ci
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


def _res_with(ranges: dict) -> ExtractionResult:
    items = [
        Item(item_id=f"I.{k}", part="I", item=k, title="t", text="x", char_range=r,
             status=Status.PRESENT, confidence=Confidence(), provenance=Provenance())
        for k, r in ranges.items()
    ]
    meta = FilingMeta("", "", "", "10-K", "", None, "html", None, None)
    return ExtractionResult(meta, items, 1, {})


def test_boundary_scores_catches_drift():
    gold = {"1": [0, 1000], "1A": [1000, 2000]}
    assert boundary_scores(_res_with({"1": (0, 1000), "1A": (1000, 2000)}), gold)["match_rate"] == 1.0
    # a 200-char boundary drift drops IoU below 0.9 -> the wrong boundary becomes a number
    assert boundary_scores(_res_with({"1": (0, 800), "1A": (800, 2000)}), gold)["match_rate"] < 1.0
    # no items extracted (the M2i case) -> 0.0, not invisible
    assert boundary_scores(_res_with({}), gold)["match_rate"] == 0.0


def test_silent_failure_logic():
    clean = _result(["1", "3"], needs_review=False)
    assert is_silent_failure(clean, ["1", "3"]) is False          # recall 1.0 -> ok
    assert is_silent_failure(clean, ["1", "3", "8"]) is True       # missed 8, unflagged -> silent
    flagged = _result(["1", "3"], needs_review=True)
    assert is_silent_failure(flagged, ["1", "3", "8"]) is False    # missed but flagged -> not silent


def test_scattered_item_check():
    from sec10k.evalkit import scattered_item_check
    canon = ("Item 7. MD&A\n" + "early mda text. " * 20 + "BOUNDARY"
             + " unrelated section. " * 10 + "Critical Estimates here")
    span_end = canon.index("BOUNDARY")  # the span stops at the first fragment (scattered)
    item7 = Item(item_id="II.7", part="II", item="7", title="MD&A", text=canon[:span_end],
                 char_range=(0, span_end), status=Status.PRESENT,
                 confidence=Confidence(), provenance=Provenance())
    meta = FilingMeta("", "", "", "10-K", "", None, "html", None, None)
    r = ExtractionResult(meta, [item7], len(canon), {}, canonical_text=canon)
    # late probe sits AFTER the span -> tail dropped -> a scattered-item failure
    assert scattered_item_check(r, "7", "Critical Estimates")["inside"] is False
    # a chunk genuinely inside the span -> ok
    assert scattered_item_check(r, "7", "early mda text")["inside"] is True
    # absent item -> abstain (None)
    assert scattered_item_check(r, "1", "anything")["inside"] is None


def _result_status(statuses: dict) -> ExtractionResult:
    items = [Item(item_id=f"I.{k}", part="I", item=k, title=k, text="t", char_range=(0, 1),
                  status=st, confidence=Confidence(), provenance=Provenance())
             for k, st in statuses.items()]
    return ExtractionResult(FilingMeta("", "", "", "10-K", "", None, "html", None, None), items, 1, {})


def test_status_match_fires_on_misclassification():
    # validate-the-validator: a WRONG status (production extraction_failure where the era says the item
    # is legitimately-absent) must violate, even though presence-recall would say nothing; a correct
    # status passes.
    from sec10k.evalkit import status_match
    bad = _result_status({"7A": Status.EXTRACTION_FAILURE, "1": Status.PRESENT})
    v = status_match(bad, {"7A": ["legitimately_absent"]})["violations"]
    assert v and v[0]["item"] == "7A" and v[0]["got"] == "extraction_failure"
    good = _result_status({"1C": Status.PRESENT})
    assert status_match(good, {"1C": ["present"]})["violations"] == []
