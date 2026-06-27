# B2 — OXY char-gold PROPOSAL (HUMAN AUDIT + FREEZE required; agent does NOT freeze)

**Status:** PROPOSAL only. `boundary_gold.json` is human-only and frozen — the agent proposes these
offsets by reading the canonical; **you audit and freeze** (the char-gold discipline + guard G8).
Nothing has been written to `boundary_gold.json`.

**Filing:** OXY `0000797468-07-000027` (Occidental Petroleum, FY2006). Empty-cluster representative:
the filing is structurally clean but uses **separator-less headers** the production regex misses
(that is the A1 bug). Its correct Item boundaries are therefore well-defined and char-goldable — the
proposed accuracy-floor anchor that A1 must flip RED→GREEN at IoU 1.0.

## Proposed offsets (into the canonical; `[start, end]`, end = next item's start)

| item | proposed `[start, end]` | heading text at `start` (evidence) |
|---|---|---|
| 1  | `[12871, 23830]` | `ITEMS 1 AND 2 BUSINESS AND\nPROPERTIES` |
| 1A | `[23830, 29538]` | `ITEM\n1A RISK FACTORS` |
| 7  | `[43808, 187430]` | `ITEM\n7\n\nManagement's Discussion and Analysis of Fi…` |
| 8  | `[187430, 422000]` | `ITEM\n8 FINANCIAL STATEMENTS AND SUPPLEMENTARY DATA` |

Proposed `boundary_gold.json` entry (for you to paste **after** auditing):
```json
"oxy-fy2006": {
  "accession": "0000797468-07-000027",
  "source": "human-audited (round-4 B2; agent-proposed, human-frozen)",
  "audited": "<DATE YOU FREEZE>",
  "items": { "1": [12871, 23830], "1A": [23830, 29538], "7": [43808, 187430], "8": [187430, 422000] }
}
```

## What YOU must decide (the caveats — these are why it's a human checkpoint)
1. **Item 1 is a COMBINED heading** `ITEMS 1 AND 2 BUSINESS AND PROPERTIES` — there is **no standalone
   Item 2**. The proposed Item-1 span `[12871, 23830]` therefore covers **Business AND Properties**.
   Decide: accept as-is (Item 1 = combined, fine — none of the four gold items is Item 2), OR split at
   the internal "PROPERTIES" subheading. **Recommend accept as-is** (the combined heading is the
   filing's real structure; splitting invents a boundary the filing doesn't have).
2. **Headings span newlines** (`ITEM\n1A`, `ITEM\n7\n\n`) because words sit on separate physical lines;
   each `start` lands on the `I` of `ITEM`/`ITEMS`. Verify a couple by eye.
3. **Item 8 span is large (~234k)** — financial statements run 187430→Item 9 @422000, with no
   intervening 7A/other heading (OXY folds 7A into Item 7). Confirm that's expected.
4. **Is OXY the right char-gold pick?** Its combined Item-1/2 heading makes it slightly less "clean"
   than hoped. If you'd rather char-gold a different empty-cluster filing with fully-standalone
   headers, say so and I'll propose another (USB / GIS were also in the cluster). Items 1A/7/8 here are
   clean separator-less headers regardless.

## How to verify before freezing
Run, in the round-4 worktree (`SEC_EDGAR_USER_AGENT` set):
```python
from sec10k.ingest import fetch_10k; from sec10k.normalize import to_canonical
c,_ = to_canonical(fetch_10k(accession="0000797468-07-000027"))
for k,(s,e) in {"1":(12871,23830),"1A":(23830,29538),"7":(43808,187430),"8":(187430,422000)}.items():
    print(k, repr(c[s:s+40]), "... end:", repr(c[e:e+30]))
```
Each `start` should sit on the item's heading; each `end` should sit on the next item's heading.
