from __future__ import annotations

import re

from sec10k.items import CANONICAL_BY_KEY, CANONICAL_ORDER

# Header at a line start, e.g. "Item 7A.", "ITEM 1.", "Item 10:", "Item 1 — Business".
# The full number is captured (1-2 digits + optional A-C) so "Item 1" never swallows
# "Item 10". nbsp is already normalised to a space by normalize.to_canonical. A trailing
# separator is required to reject prose like "Item 5 of the plan"; a header with no
# separator ("Item 1 Business") is a known P0 miss handled by later phases.
# The item/number gap tolerates a SINGLE newline ("Item\n1.") so the line-anchored path
# still segments iXBRL filings that render every token on its own line (e.g. m2i-fy2023);
# a blank-line gap or no-space ("Item1.") is still rejected to avoid spurious mid-prose hits.
_SEP = re.escape("." + ":" + ")" + "-" + chr(0x2013) + chr(0x2014))
_GAP = r"(?:[ \t]+|[ \t]*\n[ \t]*)"
_HEADER_RE = re.compile(r"(?im)^[ \t>]*item" + _GAP + r"(\d{1,2}[A-C]?)\s*[" + _SEP + "]")
# A1 (round 4): a RELAXED recogniser used ONLY as a fallback when the strict pass finds nothing (the
# OXY/GIS separator-less "empty" cluster). After the number it also accepts a separator-LESS title:
# whitespace then a Title-Case/UPPER word ("ITEM 1 Business", "ITEM 7\n\nMANAGEMENT"). `(?=[A-Z])`
# rejects lowercase continuations ("Item 5 of the plan"). Confining it to the empty-fallback pass
# means clean filings (non-empty under the strict pass) are never touched -> G9 zero-collateral.
_HEADER_RE_LOOSE = re.compile(
    r"(?im)^[ \t>]*item" + _GAP + r"(\d{1,2}[A-C]?)(?:\s*[" + _SEP + r"]|\s+(?=[A-Z]))")


def _find_headers(text: str, header_re: "re.Pattern" = _HEADER_RE) -> list[tuple[str, int, int]]:
    out = []
    for m in header_re.finditer(text):
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


def _split_runs_tolerant(headers):
    """Like _split_runs but tolerates a SINGLE out-of-order intruder -- a line-start in-prose
    cross-reference the relaxed recogniser admits ("Item 10 Executive Officers" inside Item 1's
    prose). Used ONLY on the empty-cluster fallback pass. An order dip is an intruder vs a genuine
    restart (TOC -> body) by a one-element LOOKAHEAD: a dip is an intruder iff the NEXT hit resumes
    at/above the run's last order. Two dip shapes: (b) the current hit is the dip -> skip it;
    (a) the previous hit was the spike -> replace it with the current hit."""
    runs, cur = [], []
    i, n = 0, len(headers)
    while i < n:
        hdr = headers[i]
        order = CANONICAL_ORDER[hdr[0]]
        if cur and order < CANONICAL_ORDER[cur[-1][0]]:
            run_last = CANONICAL_ORDER[cur[-1][0]]
            nxt = CANONICAL_ORDER[headers[i + 1][0]] if i + 1 < n else -1
            prev = CANONICAL_ORDER[cur[-2][0]] if len(cur) >= 2 else -1
            if nxt >= run_last:        # (b) current is a lone dip; next resumes -> skip current
                i += 1
                continue
            if order >= prev:          # (a) cur[-1] was the spike -> drop it, keep current
                cur[-1] = hdr
                i += 1
                continue
            runs.append(cur)           # genuine restart
            cur = [hdr]
            i += 1
            continue
        cur.append(hdr)
        i += 1
    if cur:
        runs.append(cur)
    return runs


def _pick_body_run(runs):
    """The body run has substantial prose between consecutive item headers; the
    table-of-contents run packs headers together with almost no text between them. Pick the
    run with the most inter-header prose (tie-break: latest start). This beats a max-span
    pick (a long TOC entry barely adds inter-header prose) and an item-count pick (a body
    with fewer *recognised* headers than the TOC still has far more prose between them).
    Residual limit: a TOC whose every entry is padded with prose-like filler is out of
    scope -- real TOC entries are one short line -- and the coverage-plausibility check in
    the validation layer backstops the no-body case."""
    if not runs:
        return []

    def prose(run):
        return sum(b[1] - a[2] for a, b in zip(run, run[1:]))  # next header start - this header end

    best = max(prose(r) for r in runs)
    near = [r for r in runs if prose(r) >= 0.8 * best] if best > 0 else runs
    return max(near, key=lambda r: r[0][1])


def _build_spans(canonical_text, headers, split_runs) -> list[tuple[str, int, int]]:
    if not headers:
        return []
    run = _pick_body_run(split_runs(headers))
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


def _coverage(spans, text: str) -> float:
    return sum(e - s for _, s, e in spans) / len(text) if text else 0.0


def segment(canonical_text: str) -> list[tuple[str, int, int]]:
    """Tier-1 anchor segmentation. Returns [(item_key, start, end)] whose spans tile the document
    from the first body item to the end.

    LAYERED PASSES, each refining the best-so-far under a guard that can only ADD recovery, never
    trade it away -- so clean filings stay byte-identical and every widen is G9 zero-collateral by
    construction (round-3 lesson + G9):
      strict   : separator-required regex + ordered run split (the byte-identical baseline).
      A1 (r4)  : if strict yields nothing, the relaxed separator-less recogniser + intruder-tolerant
                 split (the OXY/GIS empty cluster).
      A2 (r4)  : if Item 1 is dropped by an in-prose cross-reference fragmenting the run, retry the
                 strict hits with the intruder-tolerant split, kept only if Item 1 is recovered.
      A3 (r5)  : if the strict result under-segments (separator-less / iXBRL token-per-line headers,
                 Part III the strict regex missed), keep the relaxed candidate ONLY if it is a strict
                 SUPERSET of the current keys + coverage does not drop.
    Remaining P0 limits go to later phases (independent second extractor + validation layer)."""
    spans = _build_spans(canonical_text, _find_headers(canonical_text, _HEADER_RE), _split_runs)
    if not spans:
        return _build_spans(
            canonical_text, _find_headers(canonical_text, _HEADER_RE_LOOSE), _split_runs_tolerant)
    # A2 (round 4): when an in-prose cross-reference (e.g. "Item 1A. Risk Factors", "Item 4-08(g)")
    # is matched as a header, it fragments the run and the lead item is dropped. If Item 1 is missing,
    # retry the SAME (strict) header hits with the intruder-tolerant split, and keep it ONLY if it
    # recovers Item 1 without losing coverage -- so a genuinely Item-1-absent filing is never forced.
    if "1" not in {k for k, _, _ in spans}:
        retry = _build_spans(canonical_text, _find_headers(canonical_text, _HEADER_RE), _split_runs_tolerant)
        if "1" in {k for k, _, _ in retry} and _coverage(retry, canonical_text) >= _coverage(spans, canonical_text):
            spans = retry
    # A3 (round 5): the strict result has its lead item but may UNDER-segment (separator-less house
    # styles, iXBRL token-per-line headers, Part III items the strict separator missed). Compute the
    # relaxed candidate and keep it ONLY if (a) it is a strict SUPERSET of the current keys (no item
    # lost), (b) every SHARED item keeps its exact start offset -- so the relaxed pass may only INSERT
    # newly-found items into the strict skeleton, never RELOCATE an existing one (without (b), the
    # tolerant split can drop a genuine body Item 1 as a false intruder and re-anchor it on the TOC
    # line while still "keeping" the key) -- and (c) coverage does not drop. Over-drop cases are not
    # supersets and are rejected. Confining the widen to strict-dominated filings whose anchors are
    # stable keeps clean filings byte-identical (G9 zero-collateral by construction).
    relax = _build_spans(canonical_text, _find_headers(canonical_text, _HEADER_RE_LOOSE), _split_runs_tolerant)
    strict_at = {k: s for k, s, _ in spans}
    relax_at = {k: s for k, s, _ in relax}
    if set(strict_at) < set(relax_at) and all(relax_at[k] == s for k, s in strict_at.items()) and \
            _coverage(relax, canonical_text) >= _coverage(spans, canonical_text):
        return relax
    return spans
