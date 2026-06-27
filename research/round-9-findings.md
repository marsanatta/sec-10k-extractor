# Autoresearch Round 9 — Findings (fresh held-out sweep3 + generalization validation)

Goal (overnight auto mode): run a SECOND, fresh, held-out ~1000-filing sweep with ALL fixes
(A1–A4 + round-8) to validate generalization on data never seen before, then dig out any new cluster.

## The sampler hang — root-caused and fixed (per-stratum process isolation)

The first sweep3 attempts hung indefinitely (470MB, flat CPU) at the 4th stratum. eng-debug: a fresh
per-year process fetches every year 2019–2026 in ~6s each, but the full sampler accumulates ~25 years
of edgartools index tables in one process and past ~470MB a later `get_filings` stalls. Fix: a
`SWEEP_ONLY_STRATUM` mode runs ONE stratum in a fresh process and appends; the orchestrator loops the
strata so each gets a clean process (`scratch/r9_auto_sweep3b.sh`). sweep3 then completed: **881 pinned
held-out accessions** (excludes the prior 1845 + 883).

## Generalization result (the headline this round exists to produce)

**Fresh held-out sweep3 (881, ALL fixes): full 10-K structural-pass 605/656 = 92.2% (CI 89.9–94.0).**
Per era: html 91.1%, ixbrl 95.8%, sgml 92.2%; 0 fetch drops.
- This is **statistically consistent with sweep2's 93.5% (CI 91.3–95.1)** — overlapping CIs on two
  independent diverse samples. The fixes hold on data never seen during development; the headline sits
  in the ~92–94% band regardless of sample. (sweep3's draw happened to include more `empty` cases — 17
  vs 7 — so the point estimate is at the lower end, not a regression.)
- A4 + round-8 recoveries are present in sweep3 too (combined-items and Santander-type ABS pass).

## New cluster dug out: combined-header VARIANTS (round-9 fix, KEPT)

The sweep3 census exposed an energy `lead_item_1_missing` sub-cluster the narrow A4 regex missed —
real house-style variants of the combined lead header:
- `Items 1. and 2.` — a separator after the lead number (Kerr-McGee, the 0001035002 filer ×6).
- `ITEMS\n1 AND 2.` — a newline between "ITEMS" and the number (MDU).
- `Items 1., 1A. & 2.` — a longer list with "&" and commas (Valero GP).

Fix: broaden `_COMBINED_RE` to plural "Items" + the lead number with a list-connector lookahead
(and / & / , / a following digit), recovering a genuine list while rejecting singular "Item 1" (strict's
job) and prose "Items of the plan". **G9 gate: identical=1725, recovery=18, collateral=0; char-gold
gis/usb/oxy stay IoU 1.0; offline suite 98 passed / 1 skipped.** All 18 land on a real combined header.

## Still-deferred (honest — no clean cluster left in the tail)
- `empty` (17, heterogeneous: TiVo, Symyx, Cardinal Health, BellSouth, … across sectors/eras) and the
  remaining operating `lead_item_1_missing` (PBF singular-Item-1-dropped, Technitrol separator-less,
  Consumers TOC-leader-dots) are scattered one-offs, not a fixable cluster.
- BMW-type ABS (items in running "(a)/(b)" prose) + FM-4 cross-ref-index remain CRF-territory.

## Disposition
- Sampler per-stratum isolation + the combined-header variant fix KEPT (G9 zero-collateral, suite green).
- sweep3 pinned accessions + report committed (reproducible). Branch `round9/sweep3`; nothing pushed.
- A combined-variant char-gold anchor (e.g. Kerr-McGee `Items 1. and 2.`) is a candidate for a human
  bless next to oxy-fy2020 — deferred to the human (char-gold is human-only).
