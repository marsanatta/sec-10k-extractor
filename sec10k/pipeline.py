from __future__ import annotations

from sec10k.ingest import RawFiling, fetch_10k
from sec10k.items import CANONICAL_ITEMS
from sec10k.normalize import to_canonical
from sec10k.schema import ExtractionResult, FilingMeta, Item, Provenance, Status
from sec10k.segment import segment


def extract(ticker_or_cik=None, fiscal_year=None, accession=None) -> ExtractionResult:
    raw = fetch_10k(ticker_or_cik, fiscal_year, accession)
    canonical, era = to_canonical(raw)
    return _build_result(canonical, era, raw)


def extract_from_text(canonical_text: str, era: str = "html") -> ExtractionResult:
    """Run segmentation on already-normalised text (no network). Used by tests."""
    return _build_result(canonical_text, era, None)


def _build_result(canonical: str, era: str, raw: RawFiling | None) -> ExtractionResult:
    spans = {key: (s, e) for key, s, e in segment(canonical)}
    items = [
        Item(
            item_id=ci.item_id,
            part=ci.part,
            item=ci.key,
            title=ci.title,
            text=canonical[spans[ci.key][0]:spans[ci.key][1]],
            char_range=spans[ci.key],
            status=Status.PRESENT,
            provenance=Provenance(extractors=["anchor"]),
        )
        for ci in CANONICAL_ITEMS
        if ci.key in spans
    ]
    missing = [ci.key for ci in CANONICAL_ITEMS if ci.key not in spans]
    summary = {
        "items_present": len(items),
        "items_total": len(CANONICAL_ITEMS),
        "missing_keys_unclassified": missing,
        "format_era": era,
        "note": (
            "P0 tier-1 anchor segmentation. Confidence scoring, round-trip and "
            "missing-item classification (legitimately_absent vs extraction_failure) land in P1."
        ),
    }
    return ExtractionResult(
        meta=_build_meta(raw, era),
        items=items,
        canonical_text_len=len(canonical),
        summary=summary,
    )


def _build_meta(raw: RawFiling | None, era: str) -> FilingMeta:
    if raw is None:
        return FilingMeta("", "", "", "10-K", "", None, era, None, None)
    por = raw.period_of_report or ""
    fy = int(por[:4]) if len(por) >= 4 and por[:4].isdigit() else None
    return FilingMeta(
        cik=raw.cik,
        accession=raw.accession,
        company=raw.company,
        form=raw.form,
        filing_date=raw.filing_date,
        fiscal_year=fy,
        format_era=era,
        primary_document=raw.primary_document,
        source_url=raw.source_url,
    )
