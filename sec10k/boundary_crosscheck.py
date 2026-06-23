from __future__ import annotations

import difflib
import re

from sec10k.items import CANONICAL_ITEMS

_WS = re.compile(r"\s+")
_TRANS = {0x2019: "'", 0x2018: "'", 0x201C: '"', 0x201D: '"',
          0x00A0: " ", 0x2007: " ", 0x202F: " ", 0x2009: " ", 0x200A: " "}
_MIN_LEN = 1500   # only judge substantial items; small/Part-III items are bound
                  # differently by independent tools even when correct -> abstain
_RATIO = 0.6
_WINDOW = 150


def _norm(t: str) -> str:
    return _WS.sub(" ", t.translate(_TRANS).lower()).strip()


def boundary_signal(
    spans: dict[str, tuple[int, int]], canonical: str, second_text: dict[str, str]
) -> dict[str, bool | None]:
    """Independent boundary cross-check. For each item compare our span's text (head AND
    tail, where a boundary drift shows up) against a SECOND, independently produced text
    for that item. Per item: True = boundaries agree, False = disagree (likely a wrong
    boundary), None = abstain (no reliable second text, or item too small to judge).

    IMPORTANT independence caveat: this only catches a wrong boundary when our span and the
    second text DISAGREE. If the second extractor shares our blind spot (e.g. both anchor on
    the same misplaced 'Item N' header) the two agree and this check is silent -- see the
    common-mode test. A truly decorrelated second extractor (CRF) is the STRETCH upgrade."""
    out: dict[str, bool | None] = {}
    for key, (s, e) in spans.items():
        ref = second_text.get(key)
        if ref is None:
            out[key] = None
            continue
        m, r = _norm(canonical[s:e]), _norm(ref)
        if min(len(m), len(r)) < _MIN_LEN:
            out[key] = None
            continue
        head = difflib.SequenceMatcher(None, m[:_WINDOW], r[:_WINDOW]).ratio()
        tail = difflib.SequenceMatcher(None, m[-_WINDOW:], r[-_WINDOW:]).ratio()
        out[key] = head >= _RATIO and tail >= _RATIO
    return out


def edgartools_item_texts(accession: str) -> dict[str, str]:
    """Second independent extractor: edgartools' own structured item parse, looked up BY
    KEY (immune to its jumbled-order bug) with one text per key (immune to its
    duplicate-item bug). Best-effort: returns {} on any failure."""
    if not accession:
        return {}
    try:
        import edgar

        obj = edgar.get_by_accession_number(accession).obj()
    except Exception:
        return {}
    out: dict[str, str] = {}
    for ci in CANONICAL_ITEMS:
        for getter in (
            lambda k=ci.key: obj[f"Item {k}"],
            lambda k=ci.key: (obj.get_item_with_part(f"Item {k}")
                              if hasattr(obj, "get_item_with_part") else None),
        ):
            try:
                t = getter()
                if t:
                    out[ci.key] = str(t)
                    break
            except Exception:
                continue
    return out
