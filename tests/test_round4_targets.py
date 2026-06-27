"""Round-4 RED targets + regression guards (Step B — build the ruler before you cut).

The `xfail(strict=True)` tests are the FIX TARGETS: RED on current code, so the offline suite stays
green now; when the matching A-fix lands they flip to XPASS, and strict=True turns an unexpected pass
into a FAILURE — forcing the implementer to delete the marker. That is the clean RED→GREEN signal.

The plain (non-xfail) tests are REGRESSION GUARDS: they pass now and MUST keep passing after the fix
(the no-false-header / clean-case controls G9 + B4 are built around). Network-free, offline CI."""
import os

import pytest

from eval.structural_sweep import _starts_with_header
from sec10k.segment import segment


def _keys(canonical: str):
    return sorted(k for k, _, _ in segment(canonical))


# --- A1: separator-less header recogniser (empty cluster, ~67) ---------------------------------

_SEPLESS = (
    "PART I\nITEM 1 BUSINESS\n" + "We make products. " * 20 + "\n"
    "ITEM 1A RISK FACTORS\n" + "Risks exist. " * 20 + "\n"
    "ITEM 7\n\nMANAGEMENT DISCUSSION\n" + "MD&A text. " * 20 + "\n"
    "ITEM 8 FINANCIAL STATEMENTS\n" + "Financials. " * 20 + "\n"
)


def test_a1_separatorless_headers_are_found():
    # KEPT (round-4 A1, two-pass): OXY/GIS house-style headers carry NO separator after the number.
    # The strict pass returns [] on these, so segment() falls back to the relaxed recogniser and
    # recovers {1,1A,7,8}. Clean filings never reach the fallback (G9 zero-collateral).
    assert _keys(_SEPLESS) == ["1", "1A", "7", "8"]


def test_a1_control_separatored_headers_pass_today():
    # Sanity: the cooperative separator'd form already segments — A1 must not regress it.
    sepd = (_SEPLESS.replace("ITEM 1 BUSINESS", "ITEM 1. BUSINESS")
            .replace("ITEM 1A RISK", "ITEM 1A. RISK")
            .replace("ITEM 7\n\nMANAGEMENT", "ITEM 7. MANAGEMENT")
            .replace("ITEM 8 FINANCIAL", "ITEM 8. FINANCIAL"))
    assert _keys(sepd) == ["1", "1A", "7", "8"]


def test_a1_no_false_header_on_midprose_item_reference():
    # REGRESSION GUARD (must pass now AND after A1): a mid-line "in Item 8 of this report" reference
    # must NOT become a false Item-8 header. The line-start anchor already excludes it; A1's relaxed
    # recogniser must keep this true (the over-widening boundary).
    midprose = "ITEM 1. BUSINESS\n" + "Please refer to discussion in Item 8 of this report. " * 5 + "\n"
    assert _keys(midprose) == ["1"]


# --- A2: cross-reference-intruder run selection (lead_missing_high_cov + coverage_partial) -------

_CROSSREF_INTRUDER = (
    "PART I\n"
    "Item 1. Business\n" + "Short business. " * 6 + "\n"
    "Please refer to the consolidated notes in\nItem 8.\n" + "Short tail. " * 6 + "\n"
    "Item 1A. Risk Factors\n" + "Many risks indeed. " * 60 + "\n"
    "Item 7. Management Discussion And Analysis\n" + "MD&A discussion. " * 60 + "\n"
    "Item 8. Financial Statements\n" + "Financial detail. " * 60 + "\n"
)


def test_a2_inprose_crossref_does_not_drop_item_1():
    # KEPT (round-4 A2): an "Item 8." cross-reference inside a short Item-1 prose advances the
    # canonical-order counter and the strict pass drops Item 1. Because Item 1 is missing, segment()
    # retries the strict hits with the intruder-tolerant split (keeping it only if Item 1 is recovered
    # without losing coverage), so Item 1 is restored. Clean filings (Item 1 present) never retry.
    assert "1" in _keys(_CROSSREF_INTRUDER)


def test_a2_clean_case_unaffected_today():
    # REGRESSION GUARD (must pass now AND after A2): with no intruder, all items segment normally.
    clean = (
        "PART I\nItem 1. Business\n" + "Business prose. " * 30 + "\n"
        "Item 1A. Risk Factors\n" + "Risk prose. " * 30 + "\n"
        "Item 7. MD&A\n" + "MD&A prose. " * 30 + "\n"
        "Item 8. Financial Statements\n" + "Financial prose. " * 30 + "\n"
    )
    assert _keys(clean) == ["1", "1A", "7", "8"]


# --- A3: relaxed recogniser denylist (reject in-prose cross-refs, keep real edge headers) --------

def test_a3_loose_regex_rejects_inprose_crossref_keeps_real_headers():
    # KEPT (round-5 A3 + regex fix): the relaxed recogniser must reject SAME-LINE in-prose
    # cross-references ("Item 8 of this Report", "Item 1 under the caption") -- the (?i) flag once
    # defeated the uppercase guard, so A3 admitted them as headers. The same-line denylist restores
    # the guard WITHOUT dropping real edge headers that are also followed by a lowercase token:
    # combined ("Item 7 and 7A") and title-less ("Item 2\n\nAt ...", body on the next line).
    from sec10k.segment import _HEADER_RE_LOOSE as LOOSE
    assert LOOSE.match("Item 8 of this Report.") is None
    assert LOOSE.match("Item 1 under the caption Risk Factors") is None
    assert LOOSE.match("ITEM 1  Business")                       # separator-less title
    assert LOOSE.match("Item 7 and 7A   Management's Discussion")  # combined header
    assert LOOSE.match("Item 2\n\nAt February 1, 2008, we operated")  # title-less, newline-led body


# --- B5: harness predicate false-fail (COST "ITEM 1--BUSINESS", header_not_self_headed n=2) ------

def test_b5_starts_with_header_accepts_double_hyphen():
    # KEPT (round-4 B5): "ITEM 1--BUSINESS" (COST FY1999) is a real header -- production _HEADER_RE
    # accepts '-', so the sweep's self-header check now mirrors that separator set. Before B5 the
    # check used [.:)\s] (no '-') and falsely failed it, undercounting the structural-pass rate.
    assert _starts_with_header("ITEM 1--BUSINESS Costco Wholesale Corporation", 0, "1") is True


def test_a4_starts_with_header_accepts_combined_items():
    # round-7 A4 recovers Item 1 from the plural combined header "ITEMS 1 AND 2. BUSINESS AND
    # PROPERTIES" (oil/gas); the sweep's self-header check must accept it, else a correct extraction
    # is falsely flagged header:1 and the structural-pass rate undercounts the A4 recoveries.
    assert _starts_with_header("ITEMS 1 AND 2. BUSINESS AND PROPERTIES", 0, "1") is True
    assert _starts_with_header("Item 10. Directors", 0, "1") is False  # must not match 10 for key 1


# --- B3: silent-failure guard (DUK coverage_partial must FLAG, not silently pass) ---------------

@pytest.mark.skipif(not os.environ.get("SEC_EDGAR_USER_AGENT"),
                    reason="on-demand network: B3 silent-failure guard fetches DUK from EDGAR")
def test_b3_duk_coverage_partial_is_flagged_not_silent():
    # The DUK coverage_partial failure is a KNOWN-HARD case (only ~40% covered). The no-silent-failure
    # promise: it must raise needs_review, never quietly pass. Stays True before AND after any A-fix.
    from sec10k.pipeline import extract
    res = extract(accession="0001193125-11-047229")
    assert res.summary.get("needs_review") is True
