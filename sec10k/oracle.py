from __future__ import annotations

# Financial-statement section markers that Item 8 (Financial Statements) must contain.
_FIN_MARKERS = (
    "balance sheet",
    "statements of operations",
    "statements of income",
    "statements of cash flow",
    "cash flows",
    "stockholders' equity",
    "shareholders' equity",
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


def has_financial_markers(item8_text: str, min_hits: int = 2) -> bool:
    low = item8_text.lower()
    return sum(1 for m in _FIN_MARKERS if m in low) >= min_hits


def _format_candidates(value: float) -> list[str]:
    """A reported figure may be printed in dollars, thousands, or millions, with or without
    comma grouping. Generate the plausible printed forms of a raw-dollar XBRL value."""
    out: list[str] = []
    for scale in (1, 1_000, 1_000_000):
        n = abs(value) / scale
        if n < 1:
            continue
        i = int(round(n))
        out.append(f"{i:,}")
        out.append(str(i))
    return out


def values_present(xbrl_facts: dict[str, float], item8_text: str) -> tuple[int, int] | None:
    """Independent (companyfacts) oracle: of the XBRL-tagged annual facts, how many appear
    as printed figures inside the extracted Item 8 span? Returns (checked, found), or None
    if no facts were available. Tagged financial facts MUST fall inside Item 8, so found==0
    when checked>0 means the Item 8 boundary is wrong."""
    if not xbrl_facts:
        return None
    checked = found = 0
    for value in xbrl_facts.values():
        try:
            value = float(value)
        except (TypeError, ValueError):
            continue
        checked += 1
        cands = _format_candidates(value)
        if any(c in item8_text for c in cands):
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
