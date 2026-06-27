"""Offline validate-the-verifier test for the structural-sweep pass/fail predicate. The sweep
itself is network/on-demand, but its VERDICT LOGIC must be testable offline: a clean tiling
passes, and each gross-failure shape (empty, lead missing, implausible coverage, broken tiling)
must FAIL with the right reason -- a predicate that can't fail verifies nothing."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "eval"))
from structural_sweep import structural_pass  # noqa: E402

_S1 = "Item 1. Business " + "x" * 300
_S7 = "Item 7. Management Discussion " + "y" * 300
_S8 = "Item 8. Financial Statements " + "z" * 300
CANON = _S1 + _S7 + _S8
_A, _B, _L = len(_S1), len(_S1) + len(_S7), len(CANON)
CLEAN_SPANS = [("1", 0, _A), ("7", _A, _B), ("8", _B, _L)]


def test_clean_tiling_passes():
    ok, reason = structural_pass(CLEAN_SPANS, CANON)
    assert ok and reason == "ok"


def test_empty_fails():
    assert structural_pass([], CANON) == (False, "empty")


def test_lead_item_1_missing_fails():
    spans = [("7", 0, _B), ("8", _B, _L)]  # tiles fully, but no Item 1
    ok, reason = structural_pass(spans, CANON)
    assert not ok and reason == "lead_item_1_missing"


def test_implausible_coverage_fails():
    # one item covering only the last ~28% (big preamble) -> round_trip True but frac < 0.4
    start = int(0.72 * _L)
    ok, reason = structural_pass([("1", start, _L)], CANON)
    assert not ok and reason.startswith("coverage:")


def test_broken_tiling_fails():
    spans = [("1", 0, _A), ("7", _A - 20, _B)]  # overlap -> non_overlapping/contiguous broken
    ok, reason = structural_pass(spans, CANON)
    assert not ok and reason.startswith("invariant:")
