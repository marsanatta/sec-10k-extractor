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
    assert s["escalation_applied"] == 0  # deferred stub applies no correction (byte-identical)
    assert s["llm_touched"] is False     # observability: no real call fired
    assert s["escalation_items_moved"] == []


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


class _LineMock:
    """Returns a fixed line number as its boundary answer, so a test can inject the CORRECT line."""

    name = "mock-line"

    def __init__(self, line_no: int):
        self.line_no = line_no

    def adjudicate(self, prompt: str) -> Adjudication:
        return Adjudication(text=str(self.line_no), input_tokens=10, output_tokens=2)


def _iou(a, b):
    inter = max(0, min(a[1], b[1]) - max(a[0], b[0]))
    union = (a[1] - a[0]) + (b[1] - b[0]) - inter
    return inter / union if union else 0.0


def test_escalation_apply_moves_boundary_to_correct_offset():
    """INDEPENDENT boundary-correction gate (NOT token accounting): inject a deliberately-WRONG
    boundary, have the mock return the CORRECT line, and assert the span MOVES to the
    known-correct offset (IoU >= 0.9). The reference is the item's true start from a clean
    extract -- independent of the escalation path."""
    result = extract_from_text(DOC, fiscal_year=2024)
    canonical = result.canonical_text
    it = next(i for i in result.items if i.status.value == "present" and i.char_range)
    true_start, end = it.char_range                      # known-correct reference
    wrong_start = true_start + 40                         # inject a wrong boundary (within window)
    assert wrong_start < end
    it.char_range = (wrong_start, end)
    it.text = canonical[wrong_start:end]
    it.confidence.band = Band.MEDIUM                      # make it an escalation candidate

    lo = max(0, wrong_start - 2000)
    hi = min(len(canonical), wrong_start + 2000)
    off, line_no = lo, None
    for i, ln in enumerate(canonical[lo:hi].splitlines(keepends=True)):
        if off == true_start:
            line_no = i
            break
        off += len(ln)
    assert line_no is not None, "true start must be a line boundary in the window"

    out = run_escalation(result, canonical, _LineMock(line_no))
    assert out["escalation_applied"] >= 1
    assert out["llm_touched"] is True                    # observability: a real call fired+applied
    assert it.item in out["escalation_items_moved"]      # and this item is recorded as moved
    assert it.char_range[0] == true_start                # boundary moved back to the correct start
    assert _iou(it.char_range, (true_start, end)) >= 0.9  # proven against the independent reference


def test_escalation_apply_rejects_malformed_answer():
    """A malformed / out-of-range line answer must be rejected -- the boundary never degrades."""
    result = extract_from_text(DOC, fiscal_year=2024)
    it = next(i for i in result.items if i.status.value == "present" and i.char_range)
    it.confidence.band = Band.MEDIUM
    before = it.char_range

    class _BadMock:
        name = "mock-bad"

        def adjudicate(self, prompt: str) -> Adjudication:
            return Adjudication(text="not-a-line", input_tokens=5, output_tokens=1)

    out = run_escalation(result, result.canonical_text, _BadMock())
    assert out["escalation_calls"] >= 1     # the call (and token cost) still happened
    assert out["escalation_applied"] == 0   # but nothing was applied
    assert it.char_range == before          # boundary unchanged
