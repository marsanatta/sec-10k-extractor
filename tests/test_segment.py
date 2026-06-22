from sec10k.pipeline import extract_from_text
from sec10k.schema import Status
from sec10k.segment import segment

# A synthetic 10-K with a table of contents followed by the real body. The TOC lists the
# same item headers as the body, so the segmenter must pick the body run, not the TOC.
DOC = """\
TABLE OF CONTENTS
Item 1. Business 3
Item 1A. Risk Factors 10
Item 2. Properties 20
Item 7. Management's Discussion 30

PART I
Item 1. Business
We design and sell widgets. Our business spans three continents and many products.
Item 1A. Risk Factors
Competition is intense and supply chains are fragile. Risks include X, Y and Z.
Item 2. Properties
We lease offices and a warehouse in three cities under long-term agreements.
PART II
Item 7. Management's Discussion and Analysis of Financial Condition
Revenue grew ten percent year over year while operating margins expanded modestly.
"""


def test_segment_keys_in_order():
    keys = [k for k, _, _ in segment(DOC)]
    assert keys == ["1", "1A", "2", "7"]


def test_segment_picks_body_not_toc():
    spans = segment(DOC)
    item1_start = next(s for k, s, _ in spans if k == "1")
    # the chosen Item 1 must be the body occurrence (after "PART I"), not the TOC line
    assert "PART I" in DOC[:item1_start]
    assert "Business 3" not in DOC[item1_start:item1_start + 40]


def test_spans_tile_without_overlap():
    spans = segment(DOC)
    for cur, nxt in zip(spans, spans[1:]):
        assert cur[2] == nxt[1]
    assert spans[-1][2] == len(DOC)
    for _, s, e in spans:
        assert DOC[s:e].lower().lstrip().startswith("item")


def test_item_10_not_swallowed_by_item_1():
    text = (
        "PART III\n"
        "Item 10. Directors and Officers\nGovernance details here for the board.\n"
        "Item 11. Executive Compensation\nCompensation philosophy and tables follow.\n"
    )
    keys = [k for k, _, _ in segment(text)]
    assert keys == ["10", "11"]


def test_dash_separator_headers_recognised():
    em, en = chr(0x2014), chr(0x2013)
    text = (
        "PART I\n"
        f"Item 1 {em} Business\nWe build and ship products across many regions.\n"
        f"Item 2 {en} Properties\nWe lease space in several cities under agreements.\n"
    )
    assert [k for k, _, _ in segment(text)] == ["1", "2"]


def test_extract_from_text_present_and_classified():
    result = extract_from_text(DOC, fiscal_year=2024)
    present = {it.item for it in result.items if it.status == Status.PRESENT}
    assert present == {"1", "1A", "2", "7"}
    assert len(result.items) == 23  # every canonical item appears, classified
    s = result.summary
    assert s["structural_ok"] and s["round_trip_ok"]
    assert not s["unflagged_failure"]
    assert result.canonical_text_len == len(DOC)
