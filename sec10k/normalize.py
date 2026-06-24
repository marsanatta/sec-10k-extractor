from __future__ import annotations

import re

from sec10k.ingest import RawFiling

_PEM = "-----BEGIN PRIVACY-ENHANCED MESSAGE-----"
# nbsp + figure/narrow/thin/hair spaces -> plain space (codepoints, to keep source ASCII)
_SPACE_MAP = {cp: " " for cp in (0x00A0, 0x2007, 0x202F, 0x2009, 0x200A)}
_BLANKS_RE = re.compile(r"\n{3,}")
# edgartools' filing.text() occasionally returns a repr-error stub instead of the body on
# some large iXBRL filings (observed: JPM FY2023 -> 75 chars "<class ...>.__repr__ returned
# empty string"). Detect that and strip the html instead, so the canonical isn't empty.
_BROKEN_TEXT = re.compile(r"__repr__ returned empty|^\s*<class ")


def _source_text(raw: RawFiling) -> str:
    text = raw.text or ""
    html = raw.html or ""
    if html and (len(text.strip()) < 500 or _BROKEN_TEXT.search(text[:200])):
        from bs4 import BeautifulSoup

        return BeautifulSoup(html, "html.parser").get_text("\n")
    return text


def detect_era(raw: RawFiling) -> str:
    head = (raw.text or "")[:4000]
    html_low = (raw.html or "").lower()
    por = raw.period_of_report or ""
    year = int(por[:4]) if por[:4].isdigit() else None
    if _PEM in head or "<sec-document>" in head.lower() or (year is not None and year < 2001):
        return "sgml"
    if "<ix:" in html_low or "ix:nonfraction" in html_low:
        return "ixbrl"
    return "html"


def to_canonical(raw: RawFiling) -> tuple[str, str]:
    """Return (canonical_text, format_era). Item char_range offsets index into this
    canonical text; round-trip (P1) checks that item spans tile it exactly."""
    era = detect_era(raw)
    text = _source_text(raw)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.translate(_SPACE_MAP)
    lines = [ln.rstrip() for ln in text.split("\n")]
    canonical = _BLANKS_RE.sub("\n\n", "\n".join(lines))
    return canonical, era
