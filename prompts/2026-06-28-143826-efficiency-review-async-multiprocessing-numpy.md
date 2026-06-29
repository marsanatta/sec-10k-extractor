# Efficiency Review — Async / Multiprocessing / Numpy, And Easy Wins

- **Datetime:** 2026-06-28 14:38:26 Asia/Taipei
- **Summary:** Asked whether the Python implementation is efficient — do we use async / multiprocessing / numpy where it actually helps, and what are the easy wins for fetching / processing / eval — grounded by `/research` then a `/code-review` focused on efficiency.

## Prompt

> and regarding the effiency, is our python implement good? do you use async or multiprocessor or numpy if actually possible and an easy win to speed up the fetching or processing or eval? /research [nomd] as grounding and /code-review focusing on parts can be improved on efficiency /save-prompt

## What I Did

- **`/research` grounding (inline, no md file).** Established with sources that this workload is **network-bound on SEC EDGAR's hard 10 req/s cap** (exceed → ~10-min IP block). Conclusions: for I/O-bound HTTP, asyncio > threads > multiprocessing, but under a 10/s ceiling the model barely matters — the only win is sequential→concurrent up to the cap. `re` already LRU-caches compiled patterns, so module-level `re.compile` is hygiene not speed. numpy only helps for large string *arrays* (NumPy-2.0 ufuncs), not for scalar char_range/IoU — not applicable here. Verdict: **async concurrent fetch = the one real easy win; multiprocessing = premature; numpy = N/A.**
- **`/code-review` (efficiency-only, assessment, no auto-fix).** Read `ingest.py`, `run_eval.py`, `structural_sweep.py`, `segment.py`/`normalize.py`/`oracle.py`/`boundary_crosscheck.py`, `api/server.py`. Findings, each with file:line evidence:
  - **Already good (leave alone):** `structural_sweep.py:163-208` is already a bounded process pool (6 workers, `SWEEP_WORKERS`) whose multiprocessing doubles as a **hard-kill per-filing timeout** (kills zombie `to_canonical` a thread can't), with checkpointing + explicit ≤10 req/s reasoning — justified, not premature. **All regexes are module-level compiled** (segment 17/30/40, normalize 10/14, oracle 34, crosscheck 8, server 30). `ingest.py:35` has a 60s per-op HTTP timeout. `api/server.py:111` already uses `ThreadPoolExecutor(4)` + in-memory `_cache` by accession.
  - **Easy win #1 — `run_eval.py:115`:** the 27-filing eval loop is **fully sequential** (`for e in entries: rows.append(_run_one(e))`), each `_run_one`→`extract()` doing multiple EDGAR round-trips → ~10 min. Fix: bounded I/O concurrency (`ThreadPoolExecutor(4)`, or reuse the sweep's `_run_pool` for the hard-kill timeout too), ≤10 req/s → ~3-4× faster.
  - **Easy win #2 — caching gap:** no `lru_cache`/`use_local_storage`/disk cache anywhere except the API's in-memory `_cache`; every eval re-run re-fetches all 27 immutable (accession-pinned) filings — including the m2i-gold re-audit re-run, which only changed scoring. Fix: cache canonical (+companyfacts) to disk by accession → scoring-only re-runs go from ~10 min to seconds.
  - **Premature / not worth it:** multiprocessing for run_eval's CPU (it's network-bound; threads suffice — GIL released on I/O); an asyncio rewrite of ingest (edgartools is sync; a ThreadPool around the batch loop captures ~95% of the win); numpy anywhere (scalar offset math).
- **Outcome:** assessment delivered, no code changed; offered to implement win #1 (parallelize the eval fetch loop) and/or win #2 (disk cache of immutable filings). No secrets/PII in this prompt to redact.
