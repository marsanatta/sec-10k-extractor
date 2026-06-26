from __future__ import annotations

from sec10k.boundary_crosscheck import boundary_signal, edgartools_item_texts
from sec10k.dual import title_matches
from sec10k.escalation import run_escalation
from sec10k.fallback import locate_spans, needs_fallback
from sec10k.ingest import RawFiling, fetch_10k
from sec10k.items import CANONICAL_ITEMS
from sec10k.normalize import to_canonical
from sec10k.oracle import fetch_xbrl_facts
from sec10k.schema import ExtractionResult, FilingMeta, Item, Provenance, Status
from sec10k.segment import segment
from sec10k.template import FilerProfile
from sec10k.validate import assess


def extract(ticker_or_cik=None, fiscal_year=None, accession=None, llm_client=None, llm_model=None) -> ExtractionResult:
    raw = fetch_10k(ticker_or_cik, fiscal_year, accession)
    canonical, era = to_canonical(raw)
    second = edgartools_item_texts(raw.accession)
    return _build_result(canonical, era, raw, llm_client=llm_client, second_text=second, llm_model=llm_model)


def extract_from_text(
    canonical_text: str, era: str = "html", fiscal_year=None, smaller_reporting=None,
    llm_client=None, second_text=None, llm_model=None,
) -> ExtractionResult:
    """Run the pipeline on already-normalised text (no network). Used by tests."""
    return _build_result(canonical_text, era, None, fiscal_year, smaller_reporting, llm_client, second_text, llm_model)


def _present_items(canonical: str, second_text: dict | None = None):
    spans = {key: (s, e) for key, s, e in segment(canonical)}
    extractor = "anchor"
    # Tier-2 fallback: when the regex result is unusable (empty / collapsed), recover the
    # boundaries from edgartools' structured items, located back in our canonical.
    if second_text and needs_fallback(spans, canonical):
        fb = locate_spans(canonical, second_text)
        if fb and not needs_fallback(fb, canonical):
            spans, extractor = fb, "edgartools-fallback"
    items = [
        Item(
            item_id=ci.item_id, part=ci.part, item=ci.key, title=ci.title,
            text=canonical[spans[ci.key][0]:spans[ci.key][1]], char_range=spans[ci.key],
            status=Status.PRESENT, provenance=Provenance(extractors=[extractor]),
        )
        for ci in CANONICAL_ITEMS
        if ci.key in spans
    ]
    return items, spans


def _build_result(canonical, era, raw, fiscal_year=None, smaller_reporting=None, llm_client=None, second_text=None, llm_model=None):
    meta = _build_meta(raw, era)
    present, spans = _present_items(canonical, second_text)
    profile = FilerProfile(
        fiscal_year=meta.fiscal_year if raw else fiscal_year,
        smaller_reporting=meta.smaller_reporting if raw else smaller_reporting,
        form=meta.form,
    )
    xbrl_facts = fetch_xbrl_facts(meta.cik, meta.fiscal_year) if raw is not None else {}
    boundary = boundary_signal(spans, canonical, second_text or {})
    items, summary = assess(
        present, canonical, profile, title_matches(canonical, spans), xbrl_facts, boundary
    )
    summary["format_era"] = era
    result = ExtractionResult(
        meta=meta, items=items, canonical_text_len=len(canonical), summary=summary,
        canonical_text=canonical,
    )
    summary.update(run_escalation(result, canonical, llm_client, llm_model))
    return result


def _build_meta(raw: RawFiling | None, era: str) -> FilingMeta:
    if raw is None:
        return FilingMeta("", "", "", "10-K", "", None, era, None, None, None)
    por = raw.period_of_report or ""
    fy = int(por[:4]) if len(por) >= 4 and por[:4].isdigit() else None
    return FilingMeta(
        cik=raw.cik, accession=raw.accession, company=raw.company, form=raw.form,
        filing_date=raw.filing_date, fiscal_year=fy, format_era=era,
        primary_document=raw.primary_document, source_url=raw.source_url,
        smaller_reporting=raw.smaller_reporting,
    )
