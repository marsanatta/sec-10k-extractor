from sec10k.evalkit import classification_match_rate
from sec10k.pipeline import extract_from_text
from sec10k.schema import Status

DOC = (
    "TABLE OF CONTENTS\nItem 1. Business 3\nItem 3. Legal 9\n"
    "PART I\nItem 1. Business\n" + "We make and sell products worldwide. " * 30 + "\n"
    "Item 3. Legal Proceedings\n" + "Various legal matters are pending. " * 30 + "\n"
)


def _gold_from_current(result):
    """A reference that AGREES with current production categories (base match-rate 1.0). Used
    ONLY to test the SCORER mechanism -- the real Signal D uses the human-audited reference."""
    g = {}
    for it in result.items:
        if it.status == Status.PRESENT:
            g[it.item] = "present"
        elif it.status == Status.LEGITIMATELY_ABSENT:
            g[it.item] = "legitimately-absent"
    return g


def test_classification_scorer_matches_when_correct():
    result = extract_from_text(DOC, fiscal_year=2024)
    out = classification_match_rate(result, _gold_from_current(result))
    assert out["match_rate"] == 1.0 and out["total"] >= 3


def test_classification_signal_d_mutation_refutation_3a():
    """Control 3a (validate-the-signal): a DELIBERATELY-WRONG classification MUST lower Signal D.
    If a wrong classification does not move it, the signal measures nothing and must be rejected."""
    result = extract_from_text(DOC, fiscal_year=2024)
    gold = _gold_from_current(result)
    base = classification_match_rate(result, gold)["match_rate"]
    assert base == 1.0
    victim = next(it for it in result.items if it.status == Status.PRESENT)
    victim.status = Status.LEGITIMATELY_ABSENT  # over-broad "excuse" of a genuinely-present item
    after = classification_match_rate(result, gold)["match_rate"]
    assert after < base  # Signal D FELL -> it can refute, not merely confirm


def test_classification_failure_is_a_mismatch_against_ok_absent():
    """The form-blind bug shape: gold says ok-absent (out-of-amendment-scope) but production says
    failure -> mismatch. This is exactly the amendment cell the form-aware fix would correct."""
    result = extract_from_text(DOC, fiscal_year=2024)
    fail = next(it for it in result.items if it.status == Status.EXTRACTION_FAILURE)
    out = classification_match_rate(result, {fail.item: "legitimately-absent"})
    assert out["match_rate"] == 0.0
    assert out["mismatches"][0] == {"item": fail.item, "gold": "ok-absent", "prod": "failure"}
