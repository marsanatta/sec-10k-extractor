from sec10k.ingest import RawFiling
from sec10k.normalize import detect_era
from sec10k.oracle import _format_candidates, has_financial_markers, values_present
from sec10k.schema import Band, Item, Provenance, Status
from sec10k.template import FilerProfile
from sec10k.validate import assess


def test_has_financial_markers():
    assert has_financial_markers("Consolidated Balance Sheets ... Statements of Cash Flows")
    assert not has_financial_markers("Properties: we lease offices in several cities.")


def test_format_candidates_scales():
    cands = _format_candidates(364980000000.0)
    assert "364,980" in cands and "364980" in cands  # printed in millions


def test_values_present():
    text = "Total assets 364,980 and total liabilities 308,030 (in millions)."
    facts = {"Assets": 364980000000.0, "Liabilities": 308030000000.0}
    assert values_present(facts, text) == (2, 2)
    assert values_present({}, text) is None


def _item8(text: str) -> Item:
    return Item(
        item_id="II.8", part="II", item="8",
        title="Financial Statements and Supplementary Data", text=text,
        char_range=(0, len(text)), status=Status.PRESENT,
        provenance=Provenance(extractors=["anchor"]),
    )


def test_item8_oracle_downgrades_on_mismatch():
    text = "Item 8. Financial Statements\nSee the attached note without any numbers here."
    items, summary = assess([_item8(text)], text, FilerProfile(2024), {"8": True}, {"Assets": 364980000000.0})
    assert summary["item8_xbrl_found"] == 0
    assert summary["needs_review"] is True
    out8 = next(it for it in items if it.item == "8")
    assert out8.confidence.band != Band.HIGH
    assert "xbrl_item8" in out8.provenance.checks_failed


def test_item8_oracle_confirms_on_match():
    text = (
        "Item 8. Financial Statements\nConsolidated Balance Sheets. "
        "Statements of Cash Flows. Total assets 364,980 (in millions)."
    )
    items, summary = assess([_item8(text)], text, FilerProfile(2024), {"8": True}, {"Assets": 364980000000.0})
    assert summary["item8_markers"] is True
    assert summary["item8_xbrl_found"] == 1
    out8 = next(it for it in items if it.item == "8")
    assert "xbrl_item8" in out8.provenance.checks_passed


def _raw(period, text="", html=None):
    return RawFiling(
        cik="1", accession="a", company="C", form="10-K", filing_date="",
        period_of_report=period, primary_document=None, source_url=None,
        smaller_reporting=None, html=html, text=text,
    )


def test_detect_era():
    assert detect_era(_raw("1995-06-30", text="MICROSOFT CORP ANNUAL REPORT")) == "sgml"
    assert detect_era(_raw("2024-09-28", html="<html><ix:nonFraction>1</ix:nonFraction></html>")) == "ixbrl"
    assert detect_era(_raw("2015-12-31", html="<html>body</html>")) == "html"
