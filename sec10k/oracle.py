from __future__ import annotations

import re

# Financial-statement section markers that Item 8 must contain. Stems are chosen to match
# singular and plural ("statement(s) of operations") and the common "earnings"/"income
# statement" variants -- matched case-insensitively as substrings.
_FIN_MARKERS = (
    "balance sheet",
    "of operation",          # statement(s) of operations
    "income statement",
    "of income",             # statement(s) of income
    "of earnings",           # statement(s) of earnings
    "of cash flow",          # statement(s) of cash flows
    "stockholders",          # stockholders' equity
    "shareholders",
    "comprehensive income",
    "financial position",
    "notes to",
)

# Headline us-gaap concepts to cross-check; tag names vary by filer, so we try several and
# use whichever resolve for the fiscal year.
_CONCEPTS = (
    "Assets",
    "Liabilities",
    "StockholdersEquity",
    "NetIncomeLoss",
    "Revenues",
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    "CashAndCashEquivalentsAtCarryingValue",
)

_NUM_TOKEN = re.compile(r"\d[\d,]*")


def has_financial_markers(item8_text: str, min_hits: int = 2) -> bool:
    low = item8_text.lower()
    return sum(1 for m in _FIN_MARKERS if m in low) >= min_hits


def _format_candidates(value: float) -> list[str]:
    """Plausible printed forms of a raw-dollar XBRL value across dollar/thousand/million
    scales. A scaled value below 3 significant digits (n < 100) is dropped: a 1-2 digit
    figure is not distinctive enough to confirm a boundary and invites coincidental hits."""
    out: list[str] = []
    for scale in (1, 1_000, 1_000_000):
        n = abs(value) / scale
        if n < 100:
            continue
        i = int(round(n))
        out.append(f"{i:,}")
        out.append(str(i))
    return out


def values_present(xbrl_facts: dict[str, float], item8_text: str) -> tuple[int, int] | None:
    """Independent (companyfacts) oracle: of the XBRL-tagged annual facts, how many appear
    as printed figures inside the extracted Item 8 span? Returns (checked, found), or None
    if no facts were available. Matching is at the NUMBER-TOKEN level (not raw substring),
    so a candidate equals a whole printed figure -- '5000' never matches inside '15000',
    and '364980' never matches inside '9364980123'. Tagged facts MUST fall inside Item 8,
    so found==0 when checked>0 means the Item 8 boundary is wrong."""
    if not xbrl_facts:
        return None
    tokens = {m.group(0).replace(",", "") for m in _NUM_TOKEN.finditer(item8_text)}
    checked = found = 0
    for value in xbrl_facts.values():
        try:
            value = float(value)
        except (TypeError, ValueError):
            continue
        checked += 1
        cands = {c.replace(",", "") for c in _format_candidates(value)}
        if cands & tokens:
            found += 1
    return (checked, found) if checked else None


def fetch_xbrl_facts(cik: str | None, fiscal_year: int | None) -> dict[str, float]:
    """Pull a few headline annual facts from the companyfacts API (an independent data
    source) for the cross-check. Best-effort: returns {} on any failure or when offline."""
    if not cik or fiscal_year is None:
        return {}
    try:
        import edgar

        cf = edgar.get_company_facts(str(cik).zfill(10))
    except Exception:
        return {}
    out: dict[str, float] = {}
    for concept in _CONCEPTS:
        try:
            fact = cf.get_annual_fact(concept, fiscal_year)
            val = getattr(fact, "value", None) if fact is not None else None
            if val is not None:
                out[concept] = float(val)
        except Exception:
            continue
    return out
