"""SPIKE: a DECORRELATED third boundary cross-check via edgar-corpus.

Our production boundary cross-check is regex-vs-edgartools -- but edgartools is now IN the
extraction path (the Tier-2 fallback), so the two are correlated (~97% agreement in ANALYSIS):
when both are wrong the same way the cross-check stays green and lies. `eloukas/edgar-corpus`
(WWW-2025 / edgar-crawler lineage, HF) segments 10-Ks into item TEXT with an independent
toolkit -- a third, *decorrelated* signal.

What it is / isn't (honest): edgar-corpus is LOSSY (it cleans/normalises text, so it does not
char-match our canonical exactly), covers only **1993-2020**, and gives **text, not offsets**.
So we LOCATE each section's head in OUR canonical by normalized text-match -- the same trick the
fallback uses, NEVER copying its offsets -- to get an approximate start, then report three-way
agreement. It does **not** replace the human-audited char-exact gold (that stays the floor at 5
filings) and is **not** auto-frozen into gold. On-demand only (HF download) -- never the CI gate.

Run (needs `pip install "datasets<3"` -- edgar-corpus is a script-based HF dataset that
datasets 3.x dropped): SEC_EDGAR_USER_AGENT="Name email" python eval/edgar_corpus_spike.py
"""
from __future__ import annotations

import datetime
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sec10k.boundary_crosscheck import edgartools_item_texts
from sec10k.fallback import _norm_index
from sec10k.pipeline import extract

# overlapping eval filings (edgar-corpus covers 1993-2020): (id, accession, cik, filing-year)
TARGETS = [
    ("msft-fy1995", "0000891020-95-000433", 789019, 1995),
    ("ge-fy2009", "0000040545-10-000010", 40545, 2010),
    ("xom-fy2010", "0001193125-11-050134", 34088, 2011),
]
ITEMS = ["1", "1A", "7"]
SECTION = {"1": "section_1", "1A": "section_1A", "7": "section_7"}
TOL = 250  # chars: located starts within this point at the same header -> agree


def _locate_start(cnorm: str, omap: list[int], text: str | None) -> int | None:
    if not text:
        return None
    ntxt, _ = _norm_index(text)
    anchor = ntxt[:140].strip()
    if len(anchor) < 40:
        return None
    pos = cnorm.find(anchor)
    if pos == -1:
        pos = cnorm.find(anchor[:60])
    return omap[pos] if pos != -1 else None


def _edgar_corpus_sections(cik: int, year: int):
    from datasets import load_dataset
    for y in (year, year - 1, year + 1):
        try:
            ds = load_dataset("eloukas/edgar-corpus", f"year_{y}", split="train",
                              streaming=True, trust_remote_code=True)
        except Exception:
            continue
        scanned = 0
        for ex in ds:
            scanned += 1
            try:
                if int(ex.get("cik")) == int(cik):
                    return {k: ex.get(SECTION[k], "") for k in ITEMS}, y
            except (TypeError, ValueError):
                pass
            if scanned >= 8000:
                break
    return None, None


def main() -> int:
    out = []
    for fid, acc, cik, year in TARGETS:
        print(f"[spike] {fid} ...", file=sys.stderr, flush=True)
        r = extract(accession=acc)
        canon = r.canonical_text
        cnorm, omap = _norm_index(canon)
        our = {it.item: it.char_range[0] for it in r.items
               if it.status.value == "present" and it.char_range}
        edg_txt = edgartools_item_texts(acc)
        edg = {k: _locate_start(cnorm, omap, edg_txt.get(k)) for k in ITEMS}
        sections, found_year = _edgar_corpus_sections(cik, year)
        if sections is None:
            out.append((fid, None, "edgar-corpus: CIK not found near year %d" % year))
            continue
        corp = {k: _locate_start(cnorm, omap, sections.get(k)) for k in ITEMS}
        for k in ITEMS:
            o, e, c = our.get(k), edg.get(k), corp.get(k)
            present = [x for x in (o, e, c) if x is not None]
            spread = (max(present) - min(present)) if len(present) >= 2 else None
            agree3 = None not in (o, e, c) and spread is not None and spread < TOL
            consensus = [x for x in (o, e) if x is not None]
            flag = c is not None and bool(consensus) and min(abs(c - x) for x in consensus) > TOL
            out.append((fid, k, dict(our=o, edg=e, corp=c, spread=spread,
                                     agree3=agree3, flag=flag, found_year=found_year)))
    md = _render(out)
    (Path(__file__).parent / "edgar_corpus_spike.md").write_text(md, encoding="utf-8")
    print(md)
    return 0


def _render(out: list) -> str:
    rd = (datetime.datetime.utcfromtimestamp(time.time()) + datetime.timedelta(hours=8)).strftime(
        "%Y-%m-%d %H:%M Asia/Taipei")
    rows = [r for r in out if r[1] is not None]
    n3 = sum(1 for _, _, d in rows if d["agree3"])
    nflag = sum(1 for _, _, d in rows if d["flag"])
    lines = [
        "# edgar-corpus three-way cross-check (SPIKE)",
        "",
        f"Run: {rd}. On-demand (HF download) -- NOT the CI gate. A third DECORRELATED boundary",
        "signal (edgar-corpus, independent toolkit) vs our correlated regex+edgartools. It is",
        "lossy + text-only + 1993-2020, so located starts are APPROXIMATE; it does NOT replace the",
        "5 human-audited char-exact gold filings (still the floor) and is NOT frozen into gold.",
        "",
        f"- Item-boundaries where all three agree (<{TOL} chars): **{n3}/{len(rows)}** "
        "-> high confidence (the common-mode was NOT lying there)",
        f"- Item-boundaries where edgar-corpus DISAGREES with the regex+edgartools consensus: "
        f"**{nflag}** -> flag for human audit",
        "",
        "| filing | item | our_start | edgartools_start | edgar-corpus_start | spread | 3-way agree | flag |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for fid, k, d in out:
        if k is None:
            lines.append(f"| {fid} | - | {d} | | | | | |")
            continue
        flag = "**AUDIT**" if d["flag"] else ""
        lines.append(f"| {fid} | {k} | {d['our']} | {d['edg']} | {d['corp']} | {d['spread']} | "
                     f"{d['agree3']} | {flag} |")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
