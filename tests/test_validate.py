from sec10k.dual import title_matches
from sec10k.schema import Band, Item, Provenance, Status
from sec10k.template import (
    EXPECTED,
    MAYBE_INCORPORATED,
    NOT_YET,
    RESERVED,
    FilerProfile,
    expectation,
)
from sec10k.validate import (
    _classify_absent,
    assess,
    content_ok,
    round_trip,
    structural_invariants,
)


# --- validate-the-validator: each check must FIRE on an injected fault ---

def test_round_trip_detects_dropped_span():
    text = "AAAAABBBBBCCCCC"
    ok, frac = round_trip([(0, 5), (5, 10), (10, 15)], text)
    assert ok and frac == 1.0
    dropped, _ = round_trip([(0, 5), (10, 15)], text)  # middle chunk missing
    assert not dropped


def test_structural_detects_overlap_and_disorder():
    assert structural_invariants([(0, 5), (5, 10)]) == {
        "monotonic": True, "non_overlapping": True, "contiguous": True
    }
    assert not structural_invariants([(0, 6), (5, 10)])["non_overlapping"]  # overlap
    assert not structural_invariants([(10, 15), (0, 5)])["monotonic"]       # out of order


# --- expected-item template ---

def test_template_expectations():
    assert expectation("1C", FilerProfile(2020)) == NOT_YET
    assert expectation("1C", FilerProfile(2024)) == EXPECTED
    assert expectation("6", FilerProfile(2024)) == RESERVED
    assert expectation("10", FilerProfile(2024)) == MAYBE_INCORPORATED
    assert expectation("7A", FilerProfile(2024, smaller_reporting=True)) != EXPECTED
    assert expectation("7A", FilerProfile(2024, smaller_reporting=False)) == EXPECTED
    assert expectation("7A", FilerProfile(2024)) == EXPECTED  # unknown SRC -> flag a drop
    assert expectation("1", FilerProfile(2024)) == EXPECTED


def test_classify_absent_separates_legit_from_failure():
    items = {it.item: it for it in _classify_absent({"1", "1A"}, FilerProfile(2024))}
    assert items["1C"].status == Status.EXTRACTION_FAILURE    # FY2024 -> expected, missing
    assert items["6"].status == Status.LEGITIMATELY_ABSENT    # reserved
    assert items["10"].status == Status.LEGITIMATELY_ABSENT   # maybe incorporated by reference
    assert items["3"].status == Status.EXTRACTION_FAILURE     # expected, missing
    assert items["6"].confidence.band == Band.HIGH
    assert items["3"].confidence.band == Band.LOW
    assert items["3"].provenance.checks_failed                 # failure is flagged, not silent


def test_1c_pre_2023_is_legitimately_absent():
    items = {it.item: it for it in _classify_absent({"1"}, FilerProfile(2020))}
    assert items["1C"].status == Status.LEGITIMATELY_ABSENT


def test_content_signal():
    assert content_ok("1A", "These are our risk factors and exposures.")
    assert not content_ok("1A", "This paragraph has no signature word at all.")
    assert content_ok("16", "anything")  # no signature defined -> neutral pass


# --- dual-extractor (title-anchored) cross-check ---

def test_title_match_catches_mislabel():
    good = "Item 7. Management's Discussion and Analysis\nRevenue grew this year."
    assert title_matches(good, {"7": (0, len(good))})["7"] is True
    # a span labelled Item 7 whose prose is actually Item 8's content -> title mismatch
    wrong = "Item 7.\nConsolidated Balance Sheets and financial statements follow here."
    assert title_matches(wrong, {"7": (0, len(wrong))})["7"] is False


# --- assess-level validate-the-validator: a mis-segmentation must raise a flag ---

def test_assess_flags_implausible_coverage():
    canonical = "Business and risk." + " padding" * 500  # long doc
    tiny = Item(
        item_id="I.1", part="I", item="1", title="Business", text="Business",
        char_range=(0, 8), status=Status.PRESENT, provenance=Provenance(extractors=["anchor"]),
    )
    items, summary = assess([tiny], canonical, FilerProfile(2024), {"1": True})
    assert summary["coverage_plausible"] is False
    assert summary["needs_review"] is True
    assert all(
        it.confidence.band == Band.LOW for it in items if it.status == Status.PRESENT
    )
