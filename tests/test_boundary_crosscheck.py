from sec10k.boundary_crosscheck import boundary_signal
from sec10k.items import CANONICAL_BY_KEY
from sec10k.schema import Item, Provenance, Status
from sec10k.template import FilerProfile
from sec10k.validate import assess


def _doc():
    """Two large items with a known boundary; `second` is the correct independent text."""
    a = "Item 1. Business. " + "alpha sentence about the company. " * 200
    b = "Item 1A. Risk Factors. " + "bravo risk sentence about exposure. " * 200
    canonical = a + b
    spans = {"1": (0, len(a)), "1A": (len(a), len(canonical))}
    second = {"1": a, "1A": b}
    return canonical, spans, second


# --- the fault battery: each injected boundary fault MUST be detectable ---

def test_agree_on_correct_boundaries():
    canon, spans, second = _doc()
    assert boundary_signal(spans, canon, second) == {"1": True, "1A": True}


def test_catches_swallow_fault():
    # item1A swallows the last 200 chars of item1; tiling stays intact (the Fault-A case)
    canon, spans, second = _doc()
    end1 = spans["1"][1]
    bad = {"1": (0, end1 - 200), "1A": (end1 - 200, len(canon))}
    sig = boundary_signal(bad, canon, second)
    assert sig["1"] is False or sig["1A"] is False


def test_catches_merge_fault():
    # item1 absorbs all of item1A; item1A becomes empty
    canon, spans, second = _doc()
    end_all = spans["1A"][1]
    bad = {"1": (0, end_all), "1A": (end_all, end_all)}
    sig = boundary_signal(bad, canon, second)
    assert sig["1"] is False        # item1's tail is now item1A's text -> disagree
    assert sig["1A"] is None         # empty -> abstain, NOT a false 'agree'


def test_catches_swap_fault():
    # swap the labels of two large items
    canon, spans, second = _doc()
    bad = {"1": spans["1A"], "1A": spans["1"]}
    sig = boundary_signal(bad, canon, second)
    assert sig["1"] is False and sig["1A"] is False


def test_abstains_on_small_item():
    canon = "Item 4. Mine Safety Disclosures. Not applicable."
    spans = {"4": (0, len(canon))}
    second = {"4": "Item 4. Mine Safety. " + "z " * 2000}
    assert boundary_signal(spans, canon, second)["4"] is None


def test_abstains_without_second_text():
    canon, spans, _ = _doc()
    assert boundary_signal(spans, canon, {})["1"] is None


def test_assess_records_boundary_disagreement():
    canon, spans, _ = _doc()
    items = [
        Item(item_id=CANONICAL_BY_KEY[k].item_id, part=CANONICAL_BY_KEY[k].part, item=k,
             title=CANONICAL_BY_KEY[k].title, text=canon[s:e], char_range=(s, e),
             status=Status.PRESENT, provenance=Provenance(extractors=["anchor"]))
        for k, (s, e) in spans.items()
    ]
    all_items, summary = assess(items, canon, FilerProfile(2024), {"1": True, "1A": True}, {}, {"1": False})
    assert summary["boundary_disagreements"] == ["1"]
    assert summary["needs_review"] is True
    it1 = next(it for it in all_items if it.item == "1")
    assert "boundary_xcheck" in it1.provenance.checks_failed
