# Experimental reference — `PART <roman>`-glued lead-item recovery (NOT on main)

**Provenance.** This fix lived on the early experimental branch `autoresearch/10k-overnight` and was
**deliberately NOT adopted** by the official autoresearch rounds: main instead tracks WMT-2003 (the
filing it recovers) as a RED anchor (`eval_set.json`: `wmt-fy2003`, `expect_red: true`,
`structure: part_glued_lead_item`). It is preserved here as a **reference for a future implement
round** (the `lead_missing_low_cov` / PART-glued class in `research/round-4-plan.md`), then the branch
was deleted to keep the repo to a single line of development. NOT applied — round 4 should re-derive
it behind the independent RED→GREEN gates (a RED anchor + clean char-gold), not paste it in.

## What it does
Tolerate a `Part <roman>` heading glued to the FIRST item on one physical line — `PART I ITEM 1.`
(or `PART IITEM 1.` with the space lost) — which older HTML/SGML filings (WMT/T FY2003) emit and
which otherwise defeats the line-start anchor and silently drops the lead Item 1. The key subtlety:
the recorded header start must be the **`item` token, not the `PART` prefix** (a named `hdr` group),
else the Item 1 span would begin `"PART I ITEM 1."` — a boundary error.

## The diff (against main's `sec10k/segment.py`)
```diff
+# A "Part <roman>" prefix glued to the FIRST item on the same line ("PART I ITEM 1." or even
+# "PART IITEM 1." with the space lost) is tolerated -- older HTML/SGML filings (e.g. WMT/T FY2003)
+# put the Part heading and Item 1 on one physical line, which otherwise defeats the line-start
+# anchor and silently drops the lead item. The roman group backtracks so the glued case resolves.
 _SEP = re.escape("." + ":" + ")" + "-" + chr(0x2013) + chr(0x2014))
 _GAP = r"(?:[ \t]+|[ \t]*\n[ \t]*)"
-_HEADER_RE = re.compile(r"(?im)^[ \t>]*item" + _GAP + r"(\d{1,2}[A-C]?)\s*[" + _SEP + "]")
+_PART = r"(?:part[ \t]+[ivx]+[ \t]*)?"
+# The 'hdr' group spans from 'item' onward so the recorded header start is the item token, NOT the
+# optional Part prefix -- otherwise the Item 1 span would begin "PART I ITEM 1." (a boundary error).
+_HEADER_RE = re.compile(
+    r"(?im)^[ \t>]*" + _PART + r"(?P<hdr>item" + _GAP + r"(\d{1,2}[A-C]?)\s*[" + _SEP + "])")

 def _find_headers(text: str) -> list[tuple[str, int, int]]:
     out = []
     for m in _HEADER_RE.finditer(text):
-        key = m.group(1).upper()
+        key = m.group(2).upper()
         if key in CANONICAL_BY_KEY:
-            out.append((key, m.start(), m.end()))
+            out.append((key, m.start("hdr"), m.end()))
     return out
```

## Round-4 caveat before adopting
The current `_HEADER_RE` change interacts with round-4 fix A1 (separator-less headers): both touch the
same regex. If adopted, do it as ONE coordinated A-step with a RED anchor for the PART-glued class and
the clean char-gold held byte-exact (the `PART`-prefix must NOT shift any clean Item 1 start). Group
0 vs the named `hdr` group offset semantics must be re-checked against the `{1,1A,7,8}` self-check.
