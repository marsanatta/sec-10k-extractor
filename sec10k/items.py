"""Canonical 10-K item structure (Items 1-16 across Parts I-IV) per Regulation S-K /
Form 10-K. The list is in the order items appear in a filing; segmentation relies on
that order. Item 6 became `[Reserved]` for fiscal years ending after 2021-02-23, and
Item 1C (Cybersecurity) first appears in FY2023 reports (rule effective for fiscal years
ending on/after 2023-12-15) -- date-conditioned template logic lives in the validation
layer, not here."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CanonicalItem:
    key: str          # "1", "1A", "7A", "10" ...
    part: str         # "I" | "II" | "III" | "IV"
    title: str

    @property
    def item_id(self) -> str:
        return f"{self.part}.{self.key}"


CANONICAL_ITEMS: tuple[CanonicalItem, ...] = (
    CanonicalItem("1", "I", "Business"),
    CanonicalItem("1A", "I", "Risk Factors"),
    CanonicalItem("1B", "I", "Unresolved Staff Comments"),
    CanonicalItem("1C", "I", "Cybersecurity"),
    CanonicalItem("2", "I", "Properties"),
    CanonicalItem("3", "I", "Legal Proceedings"),
    CanonicalItem("4", "I", "Mine Safety Disclosures"),
    CanonicalItem("5", "II", "Market for Registrant's Common Equity, Related Stockholder Matters and Issuer Purchases of Equity Securities"),
    CanonicalItem("6", "II", "[Reserved]"),
    CanonicalItem("7", "II", "Management's Discussion and Analysis of Financial Condition and Results of Operations"),
    CanonicalItem("7A", "II", "Quantitative and Qualitative Disclosures About Market Risk"),
    CanonicalItem("8", "II", "Financial Statements and Supplementary Data"),
    CanonicalItem("9", "II", "Changes in and Disagreements with Accountants on Accounting and Financial Disclosure"),
    CanonicalItem("9A", "II", "Controls and Procedures"),
    CanonicalItem("9B", "II", "Other Information"),
    CanonicalItem("9C", "II", "Disclosure Regarding Foreign Jurisdictions that Prevent Inspections"),
    CanonicalItem("10", "III", "Directors, Executive Officers and Corporate Governance"),
    CanonicalItem("11", "III", "Executive Compensation"),
    CanonicalItem("12", "III", "Security Ownership of Certain Beneficial Owners and Management and Related Stockholder Matters"),
    CanonicalItem("13", "III", "Certain Relationships and Related Transactions, and Director Independence"),
    CanonicalItem("14", "III", "Principal Accountant Fees and Services"),
    CanonicalItem("15", "IV", "Exhibit and Financial Statement Schedules"),
    CanonicalItem("16", "IV", "Form 10-K Summary"),
)

CANONICAL_BY_KEY: dict[str, CanonicalItem] = {it.key: it for it in CANONICAL_ITEMS}

CANONICAL_ORDER: dict[str, int] = {it.key: i for i, it in enumerate(CANONICAL_ITEMS)}
