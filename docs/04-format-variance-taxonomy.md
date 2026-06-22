# 04 — Format-Variance Failure Taxonomy (with concrete, EDGAR-verified example filings)

研究日期: 2026-06-22
來源: EDGAR primary sources (data.sec.gov submissions API, efts.sec.gov full-text search, raw filing documents) — every CIK/accession below fetched and inspected directly.
信心程度: High. Each example was downloaded and the pathology confirmed in the actual bytes (HTTP 200 + grep of the real document), not inferred. Where a claim is a design observation rather than a fetched fact it is marked [DESIGN].

## How to read this catalog

A 10-K "item extractor" must split one filing into Items 1–16 (Parts I–IV). It fails in characteristic ways depending on (a) the **format era** of the filing and (b) specific **pathologies** that recur across eras. Each row gives a real filing you can fetch today, the exact step it stresses, and why a naive parser breaks on it.

Pipeline steps referenced below:
- **S1 Acquire/decode** — pull the primary doc; decode SGML wrapper / HTML / iXBRL.
- **S2 Normalize** — strip tags, resolve entities (`&#160;` `&#8217;`), join table cells, flatten styled spans to plain header text.
- **S3 Header detection** — find the `Item N` boundaries (line-anchored or DOM-anchored).
- **S4 Boundary assignment** — assign char ranges per item; enforce monotonic, non-overlapping, doc-covering ranges.
- **S5 Semantics** — classify `[Reserved]`, incorporation-by-reference pointers, amendment scope, omitted items.

URL convention: `https://www.sec.gov/Archives/edgar/data/{CIK}/{ACCESSION-no-dashes}/{primaryDoc}` (1990s filings use the flat `.../data/{CIK}/{ACCESSION-with-dashes}.txt` form).

---

## A. Format-era examples (the three eras every parser must span)

| # | Era / pathology | Company | CIK | Accession | FY (period) | Primary doc | Why hard / step stressed |
|---|---|---|---|---|---|---|---|
| 1 | **Pre-2001 plaintext SGML** | Microsoft Corp | 789019 | 0000891020-95-000433 | FY1995 (1995-06-30) | (none; SGML `.txt`) | `-----BEGIN PRIVACY-ENHANCED MESSAGE-----` wrapper + `<SEC-DOCUMENT>`/`<SEC-HEADER>` SGML tags. Headers are **all-caps `ITEM 1. BUSINESS`** with **irregular spacing** (`ITEM 8.  FINANCIAL` — two spaces). **Zero `<a href>` anchors** (no TOC hyperlinks). Stresses **S1** (decode wrapper, find the `<TYPE>10-K` document) and **S3** (regex must be case-insensitive + whitespace-tolerant; cannot rely on DOM). |
| 2 | **Early/mid-2000s HTML** | Microsoft Corp | 789019 | 0001193125-06-180008 | FY2006 (2006-06-30) | `d10k.htm` | First-generation EDGAR HTML (RDG/Donnelley `d10k.htm` template). Tag soup, `<PAGE>`-era artifacts, inconsistent header markup vs modern iXBRL. Stresses **S2** (HTML strip) and **S3** (DOM headers exist but are not yet the clean styled-anchor pattern of post-2018 filings). The MSFT **2001** filing `0001032210-01-501099/d10k.txt` is the even-harder *transition* case: an ASCII `.txt` with `<PAGE>` pagination markers and **no `<html>` tag** — neither pure SGML nor real HTML. |
| 3 | **Modern inline-XBRL (FY2024)** | Apple Inc. | 320193 | 0000320193-24-000123 | FY2024 (2024-09-28) | `aapl-20240928.htm` | 1.5 MB iXBRL. Item headers are nested `<div><span style="…underline"><a href="#…">Cybersecurity</a></span></div>` and the label `Item 1C.` sits in a **separate `<td>` cell** from its title `Cybersecurity`. Stresses **S2** (must join sibling cells + flatten styled spans, else the item number and title decouple) and the iXBRL fact layer is a free **S4** boundary oracle (companyfacts must fall inside Item 8). FY2025 equivalent: `0000320193-25-000079` / `aapl-20250927.htm`. |

---

## B. Structural / semantic pathologies (era-independent)

| # | Pathology | Company | CIK | Accession | FY | Evidence (verified in the real doc) | Step stressed |
|---|---|---|---|---|---|---|---|
| 4 | **Part III incorporated-by-reference from proxy** (pointer sentence, not content) | Apple Inc. | 320193 | 0000320193-24-000123 | FY2024 | Cover page: *"Portions of the Registrant's definitive proxy statement relating to its 2025 annual meeting of shareholders are incorporated by reference into Part III…"* Items 10–14 have **no body text**, only this pointer. | **S5**: extractor must emit Part III items as `incorporated_by_reference` (empty body) — NOT flag them as missing/failed. Over-eager "all 16 items must have content" invariants produce false negatives here. |
| 5 | **Item 6 `[Reserved]`** (post-2021, after SEC dropped Selected Financial Data, Reg S-K amend. 2021) | Apple Inc. | 320193 | 0000320193-24-000123 | FY2024 | TOC: `Item 6.        [Reserved]        20`. | **S5**: a present-but-empty item. Header detection (S3) must still fire; boundary (S4) is a near-zero-length span; content classifier must label `[Reserved]` not "missing". Confusing `[Reserved]` with a parse failure is a common silent error. |
| 6 | **Item 1C Cybersecurity present** (FY2023+, Reg S-K Item 106) | Apple Inc. | 320193 | 0000320193-24-000123 | FY2024 | Header `Item 1C. Cybersecurity` confirmed in body + TOC. FTS shows **5,479** 10-Ks contain `"Item 1C. Cybersecurity"` in H1-2024 alone. | **S3**: header set is **not fixed across years**; a hardcoded item enum (1,1A,1B,2…) misses 1C. Schema must be version-aware by fiscal year. |
| 7 | **Smaller reporting company: Item 7A omitted + 2-year financials** | M2i Global, Inc. | 1753373 | 0001493152-24-014827 | FY2023 | Cover checkbox `smaller reporting company` checked; `Item 7A. Quantitative and Qualitative Disclosures about Market Risk` present **but body = "Not applicable / Not required"**; financials run **2 fiscal years** not 3. Also carries `Item 1C. Cybersecurity`. | **S4/S5**: Item 7A is a near-empty stub (boundary collapses against Item 8). A 2-year (vs 3-year) financial block shifts the Item 8 boundary and breaks year-count heuristics. SRC filings are the long tail of EDGAR-CORPUS. |
| 8 | **Amended filing (10-K/A)** — partial-item scope | Chemed Corp | 19584 | 0001562762-25-000070 | FY2024 | Body: *"Amendment No. 1 on Form 10-K/A … to amend the Company's Annual Report on Form 10-K for the year … ended December 31, 2024, which was initially filed … on February 28, 2025…"* | **S5**: a 10-K/A frequently contains **only the amended items** (often just Part III or one exhibit), not all 16. Treating a /A like a full 10-K yields phantom "missing item" errors. Extractor must read the amendment-scope sentence and restrict expectations. |
| 9 | **Very large filing, huge TOC + cross-reference index** (GE-style) | General Electric (GE Aerospace) | 40545 | 0000040545-24-000027 | FY2023 (2023-12-31) | 4.0 MB HTML; 130 internal `href="#"` anchors; contains an explicit **"Form 10-K Cross Reference Index"** that maps each Item N to a page because the narrative is **not in Item order**. | **S3/S4**: items appear out of sequence; the only reliable map is the cross-reference table, not positional order. Naive "first `Item 7` heading wins" picks the TOC/cross-ref row, not the body section. (edgartools' cross-reference-detection strategy exists specifically for this shape.) |
| 10 | **No table-of-contents anchors** | Microsoft Corp | 789019 | 0000891020-95-000433 | FY1995 | `<a href>` anchor count = **0** in the entire filing. | **S3**: cannot bootstrap boundaries from a hyperlinked TOC; must fall back to line-anchored text regex. Any parser that *requires* anchors silently returns zero items here. |
| 11 | **Styled-span / NBSP item headers** | Apple Inc. | 320193 | 0000320193-24-000123 | FY2024 | Raw header = `<div><span style="…underline"><a …>Cybersecurity</a></span></div>`; TOC uses `&#160;`/NBSP runs and `&#8217;` for apostrophes; label and title live in separate `<td>`s. | **S2**: header text is fragmented across nested inline tags + non-breaking spaces. A `.get_text()` without cell-join + entity-resolution yields `Item 1C.   Cybersecurity` and breaks exact-match header regex. |
| 12 | **Reordered / fragmented item headers — the `Item 1` regex also catching `Item 10–16`** | Microsoft Corp | 789019 | 0000891020-95-000433 | FY1995 | Naive `r'ITEM \d+'` over the real bytes returns `{ITEM 1, ITEM 10, ITEM 11, ITEM 12, ITEM 13, ITEM 14, ITEM 2…9, ITEM 27}` — it captures `ITEM 27(a)/27(d)` (ERISA exhibit schedules) **and** an `ITEM 1` regex without a boundary anchor matches the start of `ITEM 10–14`. | **S3**: classic two-part trap. (a) `Item 1\b` must not greedily match `Item 1[0-6]`; (b) item-number regex must be **scoped to the filing body**, not exhibits — `ITEM 27` here is from a benefit-plan schedule, not a 10-K item. Over-capture inflates the item set and corrupts every downstream boundary. |

---

## C. Cross-cutting failure modes these examples expose

- **Silent zero-return** — a DOM/anchor-only parser returns 0 items on filings #1/#10 (no anchors) without raising. The #1 risk to instrument [DESIGN]; see `06-confidence-and-silent-failure.md`.
- **Over-capture** — the #12 regex trap inflates item count; #9 picks TOC/cross-ref rows as bodies.
- **False "missing"** — #4 (Part III pointer), #5 (`[Reserved]`), #7 (SRC stub), #8 (/A partial scope) all produce *legitimately* empty/absent items that a strict completeness invariant misreports as failures.
- **Schema drift** — #6 (Item 1C added FY2023), #5 (Item 6 reserved FY2021) prove the item enum is **fiscal-year-versioned**; hardcoding it guarantees future breakage.
- **Decoupled label/title** — #3/#11: in modern iXBRL the number and the title are different DOM nodes; normalization must rejoin them before header matching.

## D. Known additional hard cases from the literature (Lu et al. 2025, NTU itemseg)

Not re-fetched here but documented in `03-sota-segmentation-and-eval.md` — segmenters miss these:
- Allstates WorldCargo FY2002 — labels "Controls and Procedures" as Item 14 (should be 9A).
- Hub International FY2006 — Item 7A market-risk nested *inside* Part II / Item 7.
- Alternative Asset Mgmt Acquisition FY2007 — part of Item 8 placed **after** Item 15.

These are good additions to the GOLD subset (Section B of `08-eval-set-construction.md`) because they break boundary-ordering invariants in ways the EDGAR-CORPUS silver baseline also gets wrong.

## Verification log (reproducibility)

All fetched with `User-Agent: sec-10k-extractor research you@example.com`, ≤10 req/s.

| Filing | HTTP | Bytes | Pathology confirmed in-doc |
|---|---|---|---|
| MSFT 1995 `0000891020-95-000433.txt` | 200 | 189,572 | PRIVACY-ENHANCED wrapper, all-caps ITEM, 0 anchors, ITEM 27 trap |
| MSFT 2006 `…06-180008/d10k.htm` | 200 | (fetched via index) | early HTML template |
| MSFT 2001 `…01-501099/d10k.txt` | 200 | 209,482 | `<PAGE>` markers, no `<html>` |
| Apple FY2024 `…24-000123/aapl-20240928.htm` | 200 | 1,503,780 | Item 6 [Reserved], Item 1C, Part III IBR, styled-span/NBSP |
| Apple FY2025 `…25-000079/aapl-20250927.htm` | 200 | (submissions API) | modern iXBRL |
| M2i Global `…24-014827/form10-k.htm` | 200 | 615,242 | SRC, Item 7A "Not applicable", 2-yr |
| Chemed `…25-000070/che-20241231x10ka.htm` | 200 | 184,751 | 10-K/A Amendment No.1 scope sentence |
| GE FY2023 `…24-000027/ge-20231231.htm` | 200 | 4,042,237 | 4MB, 130 anchors, Cross Reference Index |
