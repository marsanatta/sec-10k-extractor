from __future__ import annotations

from dataclasses import dataclass

# Expectation for a canonical item, given the filing's fiscal year and filer profile.
EXPECTED = "expected"
OPTIONAL = "optional"                    # may legitimately be absent (e.g. Item 16 summary)
RESERVED = "reserved"                    # Item 6 post-2021: a stub, not real content
NOT_YET = "not_applicable_for_era"       # item did not exist for this filing (e.g. 1C pre-FY2023)
MAYBE_INCORPORATED = "maybe_incorporated"  # Part III items, usually incorporated by reference


@dataclass
class FilerProfile:
    fiscal_year: int | None
    smaller_reporting: bool | None = None  # None = unknown


def expectation(item_key: str, profile: FilerProfile) -> str:
    fy = profile.fiscal_year
    if item_key == "1C":  # Cybersecurity: first appears in FY2023 reports
        return EXPECTED if (fy is not None and fy >= 2023) else NOT_YET
    if item_key == "1A":  # Risk Factors became a required item for FY2005+
        return EXPECTED if (fy is None or fy >= 2005) else NOT_YET
    if item_key == "9C":  # Foreign jurisdictions (HFCAA): recent, often N/A
        return OPTIONAL if (fy is None or fy >= 2021) else NOT_YET
    if item_key == "6":   # became "[Reserved]" for fiscal years ending after 2021-02-23
        return RESERVED if (fy is None or fy >= 2021) else EXPECTED
    if item_key in {"10", "11", "12", "13", "14"}:
        return MAYBE_INCORPORATED
    if item_key == "7A":  # only a confirmed smaller reporting company may omit 7A; if the
        return OPTIONAL if profile.smaller_reporting is True else EXPECTED  # status is unknown, flag a drop rather than excuse it
    if item_key in {"1B", "4", "9B", "16"}:  # routinely "None"/"Not applicable"
        return OPTIONAL
    return EXPECTED


def is_legitimately_absent(item_key: str, profile: FilerProfile) -> bool:
    return expectation(item_key, profile) != EXPECTED
