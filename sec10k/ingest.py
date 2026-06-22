from __future__ import annotations

from dataclasses import dataclass

import edgar

from sec10k.config import get_user_agent


@dataclass
class RawFiling:
    cik: str
    accession: str
    company: str
    form: str
    filing_date: str
    period_of_report: str | None
    primary_document: str | None
    source_url: str | None
    smaller_reporting: bool | None
    html: str | None
    text: str


_identity_set = False


def _ensure_identity() -> None:
    global _identity_set
    if not _identity_set:
        edgar.set_identity(get_user_agent())
        _identity_set = True


def _select_by_fiscal_year(filings, fiscal_year: int):
    for f in filings:
        por = getattr(f, "period_of_report", None)
        if por and str(por).startswith(str(fiscal_year)):
            return f
    return None


def fetch_10k(
    ticker_or_cik: str | None = None,
    fiscal_year: int | None = None,
    accession: str | None = None,
) -> RawFiling:
    _ensure_identity()

    smaller_reporting: bool | None = None
    if accession:
        filing = edgar.get_by_accession_number(accession)
        if filing is None:
            raise ValueError(f"No filing found for accession {accession}")
    elif ticker_or_cik:
        company = edgar.Company(ticker_or_cik)
        try:
            smaller_reporting = bool(company.is_smaller_reporting_company)
        except Exception:
            smaller_reporting = None
        filings = company.get_filings(form="10-K")
        filing = _select_by_fiscal_year(filings, fiscal_year) if fiscal_year else None
        if filing is None:
            filing = filings.latest()
        if filing is None:
            raise ValueError(f"No 10-K filings found for {ticker_or_cik}")
    else:
        raise ValueError("Provide ticker_or_cik (with optional fiscal_year) or accession")

    text = filing.text() or ""
    try:
        html = filing.html()
    except Exception:
        html = None

    # filing.document is an Attachment object (str() of it is a Rich table, not a name),
    # so take the primary document's filename from the filing URL instead.
    source_url = str(getattr(filing, "filing_url", "") or getattr(filing, "url", "") or "")
    primary_document = source_url.rsplit("/", 1)[-1] if "/" in source_url else None

    return RawFiling(
        cik=str(getattr(filing, "cik", "") or ""),
        accession=str(getattr(filing, "accession_number", accession or "")),
        company=str(getattr(filing, "company", "") or ""),
        form=str(getattr(filing, "form", "10-K") or "10-K"),
        filing_date=str(getattr(filing, "filing_date", "") or ""),
        period_of_report=(str(getattr(filing, "period_of_report", "") or "") or None),
        primary_document=primary_document,
        source_url=source_url or None,
        smaller_reporting=smaller_reporting,
        html=html,
        text=text,
    )
