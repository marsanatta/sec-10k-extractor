from __future__ import annotations

import re

from sec10k.items import CANONICAL_BY_KEY, CANONICAL_ORDER

# Header at a line start, e.g. "Item 7A.", "ITEM 1.", "Item 10:", "Item 1 — Business".
# The full number is captured (1-2 digits + optional A-C) so "Item 1" never swallows
# "Item 10". nbsp is already normalised to a space by normalize.to_canonical. A trailing
# separator is required to reject prose like "Item 5 of the plan"; a header with no
# separator ("Item 1 Business") is a known P0 miss handled by later phases.
_SEP = re.escape("." + ":" + ")" + "-" + chr(0x2013) + chr(0x2014))
_HEADER_RE = re.compile(r"(?im)^[ \t>]*item[ \t]+(\d{1,2}[A-C]?)\s*[" + _SEP + "]")


def _find_headers(text: str) -> list[tuple[str, int, int]]:
    out = []
    for m in _HEADER_RE.finditer(text):
        key = m.group(1).upper()
        if key in CANONICAL_BY_KEY:
            out.append((key, m.start(), m.end()))
    return out


def _split_runs(headers):
    """Split header hits into maximal runs of non-decreasing canonical order. A 10-K's
    table of contents and its body are each one such run."""
    runs, cur, last = [], [], -1
    for key, start, hend in headers:
        order = CANONICAL_ORDER[key]
        if order >= last:
            cur.append((key, start, hend))
        else:
            runs.append(cur)
            cur = [(key, start, hend)]
        last = order
    if cur:
        runs.append(cur)
    return runs


def _pick_body_run(runs):
    """The body run follows the table of contents, and both list a comparable set of item
    headers. So among runs holding at least half the maximum header count, pick the
    latest-starting one -- the body always comes after the TOC. Using header COUNT (not
    character span) avoids being fooled by a TOC with long, padded entries that could
    out-span a terse body."""
    if not runs:
        return []
    max_count = max(len(r) for r in runs)
    rich = [r for r in runs if len(r) >= 0.5 * max_count]
    return max(rich, key=lambda r: r[0][1])


def segment(canonical_text: str) -> list[tuple[str, int, int]]:
    """Tier-1 anchor segmentation. Returns [(item_key, start, end)] whose spans tile the
    document from the first body item to the end. Known P0 limits (all addressed by later
    phases -- independent second extractor + validation layer): out-of-order items
    (cross-reference indices), header-less legacy filings, headers with no trailing
    separator, and a TOC whose entries out-span a terse body."""
    headers = _find_headers(canonical_text)
    if not headers:
        return []
    run = _pick_body_run(_split_runs(headers))
    seen, chosen = set(), []
    for key, start, _ in run:
        if key not in seen:
            seen.add(key)
            chosen.append((key, start))
    spans = []
    for i, (key, start) in enumerate(chosen):
        end = chosen[i + 1][1] if i + 1 < len(chosen) else len(canonical_text)
        spans.append((key, start, end))
    return spans
