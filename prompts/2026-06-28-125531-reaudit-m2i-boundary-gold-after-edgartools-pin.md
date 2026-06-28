# Re-audit Evidence — m2i Boundary Gold After Pinning edgartools (HUMAN ACTION REQUIRED)

- **Datetime:** 2026-06-28 (Asia/Taipei)
- **Status:** evidence prepared by the agent; the gold edit itself is **human-only** (char-gold is
  frozen, never auto-frozen from extractor output). This file is the independent evidence the human
  verifies before re-freezing.

## What happened (proven, not inferred)

`eval/boundary_gold.json` stores byte offsets. The m2i canonical text is produced by `edgartools`,
which `pyproject.toml` pinned only as `>=5.16`. Between the gold freeze (2026-06-24) and 2026-06-28
the installed edgartools drifted **5.16 -> 5.40.0**, and its iXBRL->text rendering of m2i changed:
the canonical got ~33 chars shorter before Item 1A, so the `Item\n1A.` header moved from char
**23541 -> 23508**. The frozen offsets did not move, so they now point mid-word.

Decisive isolated-venv test (same code, same immutable filing, only edgartools changed):

| edgartools | `Item\n1A.` header at | extractor item 1A | vs frozen gold `[23541, 23610]` |
|---|---|---|---|
| **5.16.3** | 23541 (`'Item\n1A. Ri'`) | (23541, 23611) | matches -> 2/2 |
| **5.40.0** | 23508 (`'Item\n1A.'`)   | (23508, 23578) | misaligned -> 1/2 |

So the gold was a correct human audit; the dependency moved the text under it. Fix chosen: **pin
`edgartools==5.40.0`** (done, `pyproject.toml`) so the canonical is reproducible, then re-freeze the
one gold entry that fell below the IoU>=0.9 threshold against the now-pinned 5.40 canonical.

## Scope: only m2i needs re-auditing

Under the pinned 5.40 canonical, every other gold filing still passes (the drift only nudged them):

| gold filing | mean IoU @ 5.40 | match-rate | needs re-audit? |
|---|---|---|---|
| apple-fy2024 | 0.996 | 4/4 | no (passes) |
| ko-fy2023 | 0.998 | 4/4 | no (passes) |
| msft-fy2023 | 0.998 | 4/4 | no (passes) |
| **m2i-fy2023** | **0.68** | **1/2** | **YES — its 69-char Item 1A stub fell below 0.9** |
| msft-fy1995 (SGML) | 1.000 | 3/3 | no (SGML unaffected) |
| gis-fy2018 | 0.999 | 4/4 | no (passes) |

## The exact edit to make (human verifies the snippets, then edits `eval/boundary_gold.json`)

For `m2i-fy2023.items`, under the pinned edgartools 5.40.0 canonical:

```
"1":  [7875, 23541]  ->  [7871, 23508]
"1A": [23541, 23610] ->  [23508, 23578]
```

Verbatim snippets at the NEW offsets (verify each is a genuine section body, not a TOC/cross-ref):

- **item 1** `[7871, 23508]`
  - HEAD `c[7871:7911]`  = `'Item\n1. Business\n\nUnless\notherwise state'`
  - TAIL `c[23468:23508]` = `'to the foregoing laws and regulations.\n\n'`  (ends just before the Item 1A header)
- **item 1A** `[23508, 23578]`
  - HEAD `c[23508:23548]` = `'Item\n1A. Risk Factors\n\nNot\nrequired for '`
  - TAIL `c[23538:23578]` = `'uired for smaller reporting companies.\n\n'`  (ends just before the Item 1B header)

Both new spans are clean header -> next-header boundaries. Keep `"source": "title-labelled-independent"`
and add/update an `"audited": "2026-06-28"` field. Do **not** change apple/ko/msft/msft-1995/gis.

## After the human re-freezes

1. `python eval/run_eval.py` -> confirm `m2i-fy2023` boundary returns to `1.0 (2/2)` and the headline
   boundary match-rate returns to `1.0 over 6 gold`.
2. Finalize the boundary numbers in `README.md` / `ANALYSIS.md` to the confirmed result (match-rate
   1.0 at IoU>=0.9; mean IoU 0.996-1.000 across the 6, never a bare "IoU 1.0").

## How to reproduce the proof

Isolated venv, no change to the main env:
```
python -m venv /tmp/v && /tmp/v/Scripts/python -m pip install edgartools==5.16.3 && \
  /tmp/v/Scripts/python -m pip install -e . --no-deps && \
  SEC_EDGAR_USER_AGENT="<name email>" /tmp/v/Scripts/python scratch/edgartools_probe.py
```
