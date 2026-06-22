from sec10k.escalation import DeferredLLMClient, build_lib_prompt
from sec10k.pipeline import extract_from_text

DOC = (
    "TABLE OF CONTENTS\nItem 1. Business 3\nItem 3. Legal 9\n"
    "PART I\nItem 1. Business\n" + "We make and sell products worldwide. " * 30 + "\n"
    "Item 3. Legal Proceedings\n" + "Various legal matters are pending. " * 30 + "\n"
)


def test_deferred_client_makes_no_call():
    c = DeferredLLMClient()
    assert c.name == "deferred"
    assert c.adjudicate("anything") is None


def test_pipeline_records_deferred_escalation():
    s = extract_from_text(DOC, fiscal_year=2024).summary
    assert s["escalation_provider"] == "deferred"
    assert s["escalation_performed"] is False
    assert isinstance(s["escalation_candidates"], list)
    assert "8" in s["escalation_candidates"]  # expected-but-missing item is a candidate


def test_deferred_escalation_annotates_candidates():
    result = extract_from_text(DOC, fiscal_year=2024)
    by_key = {it.item: it for it in result.items}
    assert "escalation_deferred" in by_key["8"].provenance.checks_failed  # not silently skipped


def test_lib_prompt_is_index_not_generate():
    text = "preamble\nItem 1. Business\nbody text\n"
    p = build_lib_prompt(text, "1", text.index("Item 1")).lower()
    assert "line number" in p and "do not write any prose" in p
