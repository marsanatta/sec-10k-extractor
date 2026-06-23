"""Build char-exact boundary gold (seed) for the big items 1/1A/7/8.

Easy filings (apple/ko/msft-fy2023): the number-regex is verifiably correct, so its
boundaries are frozen as gold (a fixed reference; a later regex regression will diverge
from it). Hard filing (m2i): the number-regex finds 0 items (headers are newline-broken
'Item\\n1. Business'), so its boundaries are located INDEPENDENTLY by title text -- a
genuinely different method, so this gold can catch what the regex/edgartools cross-check
both miss. Run once; verify the printed snippets; the JSON is the artifact."""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sec10k.ingest import fetch_10k
from sec10k.normalize import to_canonical
from sec10k.segment import segment

BIG = ["1", "1A", "7", "8"]
EASY = {"apple-fy2024": "0000320193-24-000123", "ko-fy2023": ("KO", 2023), "msft-fy2023": ("MSFT", 2023)}

gold = {}
for fid, ref in EASY.items():
    raw = fetch_10k(accession=ref) if isinstance(ref, str) else fetch_10k(ticker_or_cik=ref[0], fiscal_year=ref[1])
    canon, _ = to_canonical(raw)
    spans = {k: (s, e) for k, s, e in segment(canon)}
    gold[fid] = {"accession": raw.accession, "source": "regex-verified",
                 "items": {k: [spans[k][0], spans[k][1]] for k in BIG if k in spans}}

# m2i: locate the body 'Item N' that precedes each title (number is on its own line)
raw = fetch_10k(accession="0001493152-24-014827")
canon, _ = to_canonical(raw)
low = canon.lower()
def item_start(title_phrase, after):
    idx = low.find(title_phrase, after)
    return canon.rfind("Item", max(0, idx - 25), idx) if idx != -1 else -1
s1 = item_start("1. business", 6000)
s1a = item_start("1a. risk factors", s1 + 100)
end1a = low.find("\nitem", s1a + 50)
end1a = end1a if end1a != -1 else s1a + 4000
gold["m2i-fy2023"] = {"accession": raw.accession, "source": "title-labelled-independent",
                      "items": {"1": [s1, s1a], "1A": [s1a, end1a]}}

print("=== VERIFY m2i independent labels ===")
for k, (s, e) in gold["m2i-fy2023"]["items"].items():
    print(f"  {k}: [{s},{e}] start={canon[s:s+45]!r}")

(Path(__file__).resolve().parent / "boundary_gold.json").write_text(json.dumps(gold, indent=2))
print("\nwrote eval/boundary_gold.json with", len(gold), "filings")
