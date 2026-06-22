from __future__ import annotations

import re

from sec10k.items import CANONICAL_BY_KEY, CANONICAL_ORDER

# Header at a line start, e.g. "Item 7A.", "ITEM 1.", "Item 10:". The full number is
# captured (1-2 digits + optional A-C) so "Item 1" never swallows "Item 10". nbsp is
# already normalised to a space by normalize.to_canonical, so [ \t] suffices here.
_HEADER_RE = re.compile(r"(?im)^[ \t>]*item[ \t]+(\d{1,2}[A-C]?)\s*[.:)\-]")


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
    """The body run spans far more characters than the TOC run (real prose between
    items vs one-line TOC entries)."""
    best, best_span = [], -1
    for run in runs:
        span = run[-1][1] - run[0][1]
        if span > best_span:
            best, best_span = run, span
    return best


def segment(canonical_text: str) -> list[tuple[str, int, int]]:
    """Tier-1 anchor segmentation. Returns [(item_key, start, end)] whose spans tile the
    document from the first body item to the end. Known P0 limits: out-of-order items
    (e.g. cross-reference indices) and header-less legacy filings are addressed by later
    phases (independent second extractor + validation layer)."""
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
