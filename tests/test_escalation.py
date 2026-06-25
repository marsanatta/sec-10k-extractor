from sec10k.escalation import (
    Adjudication,
    DeferredLLMClient,
    build_lib_prompt,
    run_escalation,
)
from sec10k.pipeline import extract_from_text
from sec10k.schema import Band

DOC = (
    "TABLE OF CONTENTS\nItem 1. Business 3\nItem 3. Legal 9\n"
    "PART I\nItem 1. Business\n" + "We make and sell products worldwide. " * 30 + "\n"
    "Item 3. Legal Proceedings\n" + "Various legal matters are pending. " * 30 + "\n"
)


class _MockLLM:
    """Offline stand-in for a real provider: no network, emits a synthetic usage payload so
    the per-filing token ledger can be exercised without a wired LLM."""

    name = "mock"

    def __init__(self):
        self.calls = 0

    def adjudicate(self, prompt: str) -> Adjudication:
        self.calls += 1
        return Adjudication(text="0", input_tokens=len(prompt) // 4, output_tokens=3)


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


def test_deferred_ledger_is_zero_not_exercised():
    s = extract_from_text(DOC, fiscal_year=2024).summary
    assert s["escalation_performed"] is False
    assert s["escalation_calls"] == 0
    assert s["escalation_input_tokens"] == 0
    assert s["escalation_output_tokens"] == 0


def test_mock_client_token_ledger_is_summed():
    result = extract_from_text(DOC, fiscal_year=2024)
    present = next(it for it in result.items if it.status.value == "present")
    present.confidence.band = Band.MEDIUM  # force a present low-confidence boundary candidate
    mock = _MockLLM()
    out = run_escalation(result, result.canonical_text, mock)
    assert out["escalation_provider"] == "mock"
    assert out["escalation_performed"] is True
    assert out["escalation_calls"] == mock.calls >= 1
    assert out["escalation_input_tokens"] > 0
    assert out["escalation_output_tokens"] == 3 * out["escalation_calls"]
