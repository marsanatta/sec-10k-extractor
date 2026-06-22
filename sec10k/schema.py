from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum


class Status(str, Enum):
    PRESENT = "present"
    LEGITIMATELY_ABSENT = "legitimately_absent"
    EXTRACTION_FAILURE = "extraction_failure"


class Band(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNSCORED = "unscored"  # P0: confidence layer (P1) not yet applied


@dataclass
class Confidence:
    band: Band = Band.UNSCORED
    score: float | None = None
    signals: list[str] = field(default_factory=list)


@dataclass
class Provenance:
    extractors: list[str] = field(default_factory=list)
    checks_passed: list[str] = field(default_factory=list)
    checks_failed: list[str] = field(default_factory=list)


@dataclass
class Item:
    item_id: str          # "<part>.<key>", e.g. "II.7A" — stable across years
    part: str
    item: str             # canonical key: "1", "1A", "7A", "10" ...
    title: str
    text: str
    char_range: tuple[int, int] | None  # [start, end) into the canonical text; None if absent
    status: Status
    confidence: Confidence = field(default_factory=Confidence)
    provenance: Provenance = field(default_factory=Provenance)


@dataclass
class FilingMeta:
    cik: str
    accession: str
    company: str
    form: str
    filing_date: str
    fiscal_year: int | None
    format_era: str               # "sgml" | "html" | "ixbrl"
    primary_document: str | None
    source_url: str | None


@dataclass
class ExtractionResult:
    meta: FilingMeta
    items: list[Item]
    canonical_text_len: int
    summary: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = asdict(self)
        # Enums serialise to their .value via asdict on (str, Enum) members.
        return d
