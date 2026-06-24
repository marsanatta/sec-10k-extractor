"""Fallback boundary recovery from edgartools' structured item parse.

The regex/anchor segmenter is primary -- clean and $0 on the cooperative common case. But some
real structures defeat it: the body collapses into one item (GE FY2009 -> Item 8 = 314KB), or
nothing segments at all. When that happens we recover boundaries from edgartools' .obj().items
(already fetched for the cross-check). edgartools gives item TEXT on a different char stream, so
to keep our char_range contract we LOCATE each item's head back in OUR canonical by normalized
text match and tile -- we never copy edgartools' offsets.
"""

from __future__ import annotations

import re

_TRANS = {0x2019: "'", 0x2018: "'", 0x201C: '"', 0x201D: '"', 0x00A0: " ", 0x2007: " ",
          0x202F: " ", 0x2009: " ", 0x200A: " ", 0x2013: "-", 0x2014: "-"}
_ANCHOR = 140      # head-anchor length to search for
_MIN_ANCHOR = 40


def _norm_index(text: str) -> tuple[str, list[int]]:
    """Collapse whitespace runs to one space, lowercase, fold curly quotes/dashes. Return the
    normalized string and a map from each normalized-char position to its original index."""
    out: list[str] = []
    omap: list[int] = []
    prev_ws = True
    for i, ch in enumerate(text):
        c = _TRANS.get(ord(ch), ch)
        if c.isspace():
            if not prev_ws:
                out.append(" ")
                omap.append(i)
            prev_ws = True
        else:
            out.append(c.lower())
            omap.append(i)
            prev_ws = False
    return "".join(out), omap


def needs_fallback(spans: dict[str, tuple[int, int]], canonical: str) -> bool:
    """True when the primary segmentation is unusable: nothing found, or one item collapsed
    over the document while the lead item (1) is missing (the GE-style swallow)."""
    if not spans:
        return True
    n = len(canonical) or 1
    biggest = max(e - s for s, e in spans.values())
    return biggest > 0.5 * n and "1" not in spans


def locate_spans(canonical: str, item_texts: dict[str, str]) -> dict[str, tuple[int, int]]:
    """Locate each edgartools item's head in `canonical` and tile into char ranges. Items are
    ordered by where they actually land in the canonical (immune to edgartools' jumbled order)."""
    norm, omap = _norm_index(canonical)
    starts: dict[str, int] = {}
    for key, txt in item_texts.items():
        ntxt, _ = _norm_index(txt)
        anchor = ntxt[:_ANCHOR].strip()
        if len(anchor) < _MIN_ANCHOR:
            continue
        pos = norm.find(anchor)
        if pos == -1:
            pos = norm.find(anchor[:60])
        if pos != -1:
            starts[key] = omap[pos]
    ordered = sorted(starts.items(), key=lambda kv: kv[1])
    spans: dict[str, tuple[int, int]] = {}
    for i, (key, s) in enumerate(ordered):
        end = ordered[i + 1][1] if i + 1 < len(ordered) else len(canonical)
        spans[key] = (s, end)
    return spans
