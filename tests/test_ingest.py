import pytest

import sec10k.ingest as ingest


class _FakeFiling:
    def __init__(self, period, accession):
        self.period_of_report = period
        self.accession_number = accession
        self.cik = "0000001234"
        self.company = "TEST CO"
        self.form = "10-K"
        self.filing_date = period
        self.filing_url = f"https://www.sec.gov/Archives/edgar/data/1234/{accession}/doc.htm"
        self.url = self.filing_url

    def text(self):
        return "ITEM 1. BUSINESS\nbody text."

    def html(self):
        return None


class _FakeFilings(list):
    # edgartools' .latest() returns the most recent filing; we keep newest-first.
    def latest(self):
        return self[0] if self else None


class _FakeCompany:
    filings = _FakeFilings([
        _FakeFiling("2024-12-31", "0000000000-24-000001"),
        _FakeFiling("2023-12-31", "0000000000-23-000001"),
    ])

    def __init__(self, ticker_or_cik):
        self.is_smaller_reporting_company = False

    def get_filings(self, form=None):
        return self.filings


@pytest.fixture
def fake_edgar(monkeypatch):
    monkeypatch.setattr(ingest, "_identity_set", True)  # skip set_identity / network
    monkeypatch.setattr(ingest.edgar, "Company", _FakeCompany)


def test_matching_fiscal_year_returns_that_filing(fake_edgar):
    rf = ingest.fetch_10k(ticker_or_cik="TEST", fiscal_year=2023)
    assert rf.period_of_report.startswith("2023")
    assert rf.accession == "0000000000-23-000001"


def test_no_fiscal_year_returns_latest(fake_edgar):
    rf = ingest.fetch_10k(ticker_or_cik="TEST")
    assert rf.period_of_report.startswith("2024")


def test_unmatched_fiscal_year_raises_instead_of_returning_latest(fake_edgar):
    # The fix: an explicit year with no matching filing must error, not silently
    # return the most recent 10-K (the "IBM 1995 -> FY2025" silent wrong-filing bug).
    with pytest.raises(ValueError, match="fiscal year 1995"):
        ingest.fetch_10k(ticker_or_cik="TEST", fiscal_year=1995)


def test_zero_fiscal_year_is_explicit_and_raises(fake_edgar):
    # 0 is falsy but still an explicit request -- it must match-or-raise, not return latest.
    with pytest.raises(ValueError, match="fiscal year 0"):
        ingest.fetch_10k(ticker_or_cik="TEST", fiscal_year=0)


def test_no_tenk_filings_at_all_raises(fake_edgar, monkeypatch):
    class _NoTenK(_FakeCompany):
        def get_filings(self, form=None):
            return _FakeFilings([])

    monkeypatch.setattr(ingest.edgar, "Company", _NoTenK)
    with pytest.raises(ValueError, match="No 10-K filings found"):
        ingest.fetch_10k(ticker_or_cik="TEST")
