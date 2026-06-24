from sec10k.fallback import locate_spans, needs_fallback
from sec10k.pipeline import extract_from_text
from sec10k.schema import Status


def test_needs_fallback_flags_empty_and_collapse():
    assert needs_fallback({}, "x" * 1000)                       # nothing segmented
    assert needs_fallback({"8": (0, 600)}, "x" * 1000)          # one item > 50% AND item 1 missing
    assert not needs_fallback({"1": (0, 600)}, "x" * 1000)      # lead item present -> not a collapse
    assert not needs_fallback({"1": (0, 100), "7": (100, 200)}, "x" * 1000)


def test_locate_spans_recovers_boundaries_from_item_texts():
    s1 = "Item 1. Business\n" + "The company designs and sells many products across regions. " * 4
    s7 = "Item 7. Management Discussion\n" + "Revenue grew while margins expanded modestly here. " * 4
    s8 = "Item 8. Financial Statements\n" + "See the consolidated statements and the related notes. " * 4
    canon = s1 + s7 + s8
    item_texts = {"1": s1, "7": s7, "8": s8}       # edgartools-style texts == the real bodies
    spans = locate_spans(canon, item_texts)
    assert set(spans) == {"1", "7", "8"}
    assert spans["1"][0] == canon.index("Item 1.")
    assert spans["7"][0] == canon.index("Item 7.")
    assert spans["1"][1] == spans["7"][0]          # tiles contiguously
    assert spans["8"][1] == len(canon)


def test_pipeline_engages_fallback_when_regex_cannot_segment():
    # headers are mid-line (not at a line start) so the anchor regex finds nothing, but the
    # bodies are present -> the edgartools-style second text relocates them.
    body1 = "Item 1. Business. " + "alpha " * 300
    body7 = "Item 7. MD and A. " + "beta " * 300
    canon = "intro >> " + body1 + " >> " + body7
    result = extract_from_text(canon, second_text={"1": body1, "7": body7})
    present = {it.item for it in result.items if it.status == Status.PRESENT}
    assert present == {"1", "7"}
    assert all(
        "edgartools-fallback" in it.provenance.extractors
        for it in result.items
        if it.status == Status.PRESENT
    )
