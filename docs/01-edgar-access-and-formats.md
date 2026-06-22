# SEC EDGAR Access & 10-K Format Landscape

**研究日期 (Research date):** 2026-06-22
**來源數量 (Sources):** 18 (SEC primary endpoints + live API probes + legal/practitioner refs)
**信心程度 (Confidence):** 9/10 — core access paths and format facts verified against live SEC endpoints and the official Form 10-K PDF; the long tail of layout-variance pathologies is empirically real but unbounded.

This document grounds the data-access and format assumptions for a pipeline that extracts individual Items (1–16, across Parts I–IV) from raw SEC 10-K filings. Every claim is cited. Live-probe results were captured 2026-06-22 against `data.sec.gov`, `efts.sec.gov`, and `www.sec.gov/Archives`.

---

## 1. SEC EDGAR Access

### 1.1 Fair-access policy: rate limit + User-Agent (non-negotiable)

- **Hard limit: no more than 10 requests/second**, counted per requester across all machines/IPs, not per connection. Exceeding it gets the IP throttled; the block lifts automatically after **10 minutes**. ([SEC: Accessing EDGAR Data](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data); [SEC: new rate control limits](https://www.sec.gov/filergroup/announcements-old/new-rate-control-limits))
- **A descriptive `User-Agent` header is mandatory** on every request. SEC guidance asks for a string that identifies you, conventionally `Sample Company Name AdminContact@example.com`. Requests without it (or from "unclassified bots") may be blocked. No API key, no auth token exists. ([SEC: Accessing EDGAR Data](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data); [SEC: Developer Resources](https://www.sec.gov/about/developer-resources))
- **Verified empirically:** WebFetch (default browser-like UA) gets `403 Forbidden` from `www.sec.gov`; `curl` with `-A "sec-10k-extractor research <email>"` succeeds. The UA gate is actively enforced.

```
User-Agent: sec-10k-extractor research you@example.com
```

### 1.2 The structured-data host: `data.sec.gov` (JSON APIs)

Official docs: [SEC EDGAR Application Programming Interfaces (APIs)](https://www.sec.gov/search-filings/edgar-application-programming-interfaces). No API key; same 10 req/s + UA rules apply.

| Endpoint | URL pattern | Returns |
|---|---|---|
| **Submissions** | `https://data.sec.gov/submissions/CIK##########.json` | Entity metadata + full filing history (form, date, accession, primaryDocument…) |
| **CompanyConcept** | `https://data.sec.gov/api/xbrl/companyconcept/CIK##########/us-gaap/<Concept>.json` | All values of one XBRL concept over time |
| **CompanyFacts** | `https://data.sec.gov/api/xbrl/companyfacts/CIK##########.json` | Every XBRL fact the company ever reported |
| **Frames** | `https://data.sec.gov/api/xbrl/frames/us-gaap/<Concept>/USD/CY####Q#I.json` | One concept across **all** filers for one period |

- **CIK must be zero-padded to 10 digits** in these URLs (e.g. Apple CIK 320193 → `CIK0000320193`). ([SEC APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces))
- XBRL APIs cover forms 10-Q, 10-K, 8-K, 20-F, 40-F, 6-K and variants. ([SEC APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces))

**Live-verified submissions JSON shape** (`CIK0000320193.json`, 2026-06-22):
- Top keys: `cik, entityType, sic, sicDescription, name, tickers, exchanges, fiscalYearEnd, stateOfIncorporation, formerNames, filings`.
- `filings.recent` is a **columnar/parallel-array** object — each key is an array, index `i` is one filing:
  `accessionNumber, filingDate, reportDate, acceptanceDateTime, act, form, fileNumber, items, core_type, size, isXBRL, isInlineXBRL, isXBRLNumeric, primaryDocument, primaryDocDescription`.
- When a filer's history is long, older filings spill into additional files referenced under `filings.files[]` (e.g. `CIK##########-submissions-001.json`) — you must follow those for a complete history.

### 1.3 From ticker/CIK → a specific 10-K's primary document (the canonical path)

This is the load-bearing workflow for the pipeline. Verified end-to-end live on Apple:

1. **Ticker → CIK.** Map via the static file `https://www.sec.gov/files/company_tickers.json` (ticker→CIK table). Or skip if CIK known.
2. **CIK → filing list.** `GET https://data.sec.gov/submissions/CIK0000320193.json`.
3. **Pick the 10-K.** Walk `filings.recent`, select indices where `form[i] == "10-K"`. Read `accessionNumber[i]` and `primaryDocument[i]`.
4. **Build the archive URL.** Accession `0000320193-25-000079` → strip dashes → `000032019325000079`. Then:
   - Primary iXBRL doc: `https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm`
   - Filing directory: `https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/`
   - Complete submission (dashed accession): `https://www.sec.gov/Archives/edgar/data/320193/0000320193-25-000079.txt`

Note the **two accession spellings**: directory paths use the no-dash form; the complete-submission `.txt` uses the dashed form. (Verified 2026-06-22; `isInlineXBRL=1` for this filing.)

A machine-readable directory listing is available at `…/<accession-nodash>/index.json` (live-verified — see §2.4 for the full file inventory it returned).

### 1.4 EDGAR Full-Text Search (EFTS)

- **UI:** [efts.sec.gov full-text search](https://www.sec.gov/edgar/search/). **JSON API:** `https://efts.sec.gov/LATEST/search-index?q=...`
- **Coverage starts at 2001.** "Full-Text Search will allow you to search the full text of all EDGAR filings submitted electronically **since 2001**… including all attachments (exhibits)." **Anything before 2001 is NOT full-text searchable.** ([SEC: EFTS FAQ](https://www.sec.gov/edgar/search/efts-faq.html))
- **Query params** (live-verified): `q` (term/phrase, quoted for exact), `forms` (e.g. `10-K`), `dateRange=custom` with `startdt`/`enddt` (`yyyy-mm-dd`), `ciks`. Booleans: capitalized `OR`, `NOT`/`-prefix`, `NEAR(n)`; trailing `*` wildcard (not mid-word, not in phrases). ([EFTS FAQ](https://www.sec.gov/edgar/search/efts-faq.html))
- **Live JSON shape** (probed 2026-06-22): `{ took, hits: { total: {value}, hits: [ { _id, _source: { ciks[], display_names[], period_ending, file_num[], form, file_date, ... } } ] } }`.
- **`_id` is the key to the primary document:** format is `"<dashed-accession>:<filename>"`, e.g. `0000815097-23-000012:ccl-20221130.htm`. Split on `:` and combine with the CIK to build the archive URL. Returns up to 100 hits/request (`size`), paginate with `from`. ([tldrfiling: EFTS API guide](https://tldrfiling.com/blog/sec-edgar-full-text-search-api))

### 1.5 Indexes & bulk data (avoid hammering the live APIs)

- **Quarterly full indexes:** `https://www.sec.gov/Archives/edgar/full-index/{YYYY}/QTR{n}/` — `form.idx`, `company.idx`, `master.idx` list every filing for that quarter with the path to its complete-submission `.txt`. Daily indexes under `…/full-index/{YYYY}/QTR{n}/` too. ([SEC: Accessing EDGAR Data](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data))
- **Bulk ZIPs** (regenerated nightly): `https://www.sec.gov/Archives/edgar/daily-index/bulkdata/submissions.zip` (all `submissions/*.json`) and `https://www.sec.gov/Archives/edgar/daily-index/bulkdata/companyfacts.zip` (all `companyfacts/*.json`). For corpus-scale work, download these once instead of millions of API calls. ([SEC APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces))

---

## 2. 10-K File Formats Seen In Practice

A single 10-K "filing" (one accession) is a **bundle of files**, not one document. The format of the primary document depends heavily on the filing era.

### 2.1 The complete-submission `.txt` (SGML envelope) — present in EVERY era

`…/<dashed-accession>.txt` is the full submission: an SGML envelope wrapping a header plus every constituent document. Structure (live-verified on Apple 2025 and Microsoft 1998):

```
<SEC-DOCUMENT>0000320193-25-000079.txt : 20251031
<SEC-HEADER>...
ACCESSION NUMBER:  0000320193-25-000079
CONFORMED SUBMISSION TYPE: 10-K
CONFORMED PERIOD OF REPORT: 20250927
FILER: COMPANY CONFORMED NAME: Apple Inc.  CENTRAL INDEX KEY: 0000320193 ...
</SEC-HEADER>
<DOCUMENT>
<TYPE>10-K
<FILENAME>aapl-20250927.htm
<DESCRIPTION>10-K
<TEXT> ...primary document body... </TEXT>
</DOCUMENT>
<DOCUMENT>
<TYPE>EX-4.1
<FILENAME>...
...
```

- Each constituent file is one `<DOCUMENT>` block with `<TYPE>` (e.g. `10-K`, `EX-21.1`, `GRAPHIC`), `<FILENAME>`, `<DESCRIPTION>`, and a `<TEXT>` body. **The primary 10-K is the `<DOCUMENT>` whose `<TYPE>` is `10-K`.**
- The **SGML header** is also machine-parsable for filer metadata (CIK, period, SIC) without hitting `data.sec.gov`.

### 2.2 Era 1 — Legacy plain-text (pre-~2001)

Live-verified: Microsoft FY1998 10-K (`0001032210-98-001067.txt`).
- Wrapped in a **PEM (Privacy-Enhanced Message)** preamble (`-----BEGIN PRIVACY-ENHANCED MESSAGE-----`, RSA-MD5 lines) before the `<SEC-DOCUMENT>` tag — a legacy artifact to strip.
- Body is **ASCII plain text**, ~80-column, no HTML. Headers appear as all-caps `ITEM 1. BUSINESS`, `ITEM 7a. QUANTITATIVE AND QUALITATIVE…`.
- **Item titles AND numbering differ from today.** The 1998 filing has `ITEM 4. SUBMISSION OF MATTERS TO A VOTE OF SECURITY HOLDERS`, `ITEM 6. SELECTED FINANCIAL DATA`, `ITEM 14. EXHIBITS, FINANCIAL STATEMENT SCHEDULES AND REPORTS ON FORM 8-K` — none of which match the current form. **A parser keyed to today's titles will mislabel old filings.** ([Microsoft FY1998 10-K, live](https://www.sec.gov/Archives/edgar/data/789019/0001032210-98-001067.txt))
- No XBRL, no R-files, no `FilingSummary.xml` in this era.

### 2.3 Era 2 — HTML (~2001 onward)

Primary document becomes an `.htm`/`.html` file. Carries presentational markup: `<table>`, styled `<span>`/`<font>`, `&#160;` (non-breaking space) inside headers, anchor tags for a table of contents. Noisy tags must be cleaned before text parsing. ([SRAF / Notre Dame 10-X parsing docs](https://sraf.nd.edu/sec-edgar-data/cleaned-10x-files/10x-stage-one-parsing-documentation/); [How to parse 10-K, gist](https://gist.github.com/anshoomehra/ead8925ea291e233a5aa2dcaa2dc61b2))

### 2.4 Era 3 — Inline XBRL (iXBRL), mandated and now ubiquitous

The SEC requires **Inline XBRL** tagging of the financial statements and the cover page of Forms 10-K/10-Q/20-F/40-F. iXBRL embeds machine-readable tags **directly inside the human-readable HTML** — one file serves both audiences. ([SEC: Inline XBRL](https://www.sec.gov/data-research/structured-data/inline-xbrl))

**Live-verified filing directory** (`…/000032019325000079/index.json`) for Apple's 2025 10-K shows the full modern bundle:

| File(s) | Role |
|---|---|
| `aapl-20250927.htm` | **Primary iXBRL 10-K document** (live: 1,938 `ix:nonFraction` + 324 `ix:nonNumeric` tags + an `<ix:header>`) |
| `aapl-20250927_htm.xml` | Extracted XBRL instance |
| `aapl-20250927.xsd`, `_cal.xml`, `_def.xml`, `_lab.xml`, `_pre.xml` | XBRL taxonomy schema + calculation/definition/label/presentation linkbases |
| `FilingSummary.xml` | Manifest of the rendered "Financial Report" — maps each **R-file** to a report name/section |
| `R1.htm … R26.htm…` | **R-files**: SEC-rendered HTML of each financial statement / footnote (the "Financial Report" view) |
| `MetaLinks.json` | XBRL fact metadata |
| `a10-kexhibit21*.htm`, `…exhibit23*`, `…exhibit31*`, `…exhibit32*`, `…exhibit4*` | Exhibits (subsidiaries, consent, certifications, etc.) |
| `…-index.html`, `…-index-headers.html`, `….txt`, `…-xbrl.zip` | Index pages, complete submission, zipped XBRL |

- **`FilingSummary.xml`** is the manifest tying R-files to their meaning; live-verified to reference `R1.htm…R8.htm…` via `<HtmlFileName>` under each `<Report>`. Useful for grabbing financial statements directly, but the **R-files only cover the XBRL-tagged financial statements**, NOT the Item 1/1A/7 narrative text — those live only in the primary `.htm`. ([sec-api.io: extract financial statements](https://sec-api.io/resources/extract-financial-statements-from-sec-filings-and-xbrl-data-with-python))

**Implication:** Item segmentation of the narrative (Items 1–7) must parse the **primary `.htm`** (or the `<TYPE>10-K` block of the complete `.txt`). XBRL/R-files give you the financial facts (an independent ground-truth check for the Item 8 boundary) but not the prose boundaries.

---

## 3. Official 10-K Structure Spec (Items 1–16, Parts I–IV)

**Where it is defined:** Form 10-K is promulgated under the Securities Exchange Act of 1934. The form's item instructions cross-reference **Regulation S-K (17 CFR Part 229)** for the substantive disclosure content (e.g. "Furnish the information required by Item 101 of Regulation S-K"). The form itself is the authoritative item list. ([SEC Form 10-K PDF](https://www.sec.gov/files/form10-k_1.pdf); [SEC: Regulation S-K](https://www.sec.gov/rules-regulations/staff-guidance/compliance-disclosure-interpretations/regulation-s-k))

**Item titles below are transcribed directly from the official SEC Form 10-K PDF** (`form10-k_1.pdf`, downloaded and text-extracted 2026-06-22). Item 1C is added separately (see note).

### Part I
| Item | Title | S-K ref |
|---|---|---|
| 1 | Business | Item 101 |
| 1A | Risk Factors | Item 105 |
| 1B | Unresolved Staff Comments | — |
| **1C** | **Cybersecurity** | **Item 106** |
| 2 | Properties | Item 102 |
| 3 | Legal Proceedings | Item 103 |
| 4 | Mine Safety Disclosures | — |

### Part II
| Item | Title | S-K ref |
|---|---|---|
| 5 | Market for Registrant's Common Equity, Related Stockholder Matters and Issuer Purchases of Equity Securities | Item 201/701/703 |
| **6** | **[Reserved]** | — |
| 7 | Management's Discussion and Analysis of Financial Condition and Results of Operations | Item 303 |
| 7A | Quantitative and Qualitative Disclosures About Market Risk | Item 305 |
| 8 | Financial Statements and Supplementary Data | — |
| 9 | Changes in and Disagreements With Accountants on Accounting and Financial Disclosure | Item 304 |
| 9A | Controls and Procedures | Item 307/308 |
| 9B | Other Information | — |
| 9C | Disclosure Regarding Foreign Jurisdictions that Prevent Inspections | — |

### Part III  (commonly **incorporated by reference** from the proxy statement)
| Item | Title | S-K ref |
|---|---|---|
| 10 | Directors, Executive Officers and Corporate Governance | Item 401/406/407 |
| 11 | Executive Compensation | Item 402 |
| 12 | Security Ownership of Certain Beneficial Owners and Management and Related Stockholder Matters | Item 201(d)/403 |
| 13 | Certain Relationships and Related Transactions, and Director Independence | Item 404/407 |
| 14 | Principal Accountant Fees and Services | — |

### Part IV
| Item | Title |
|---|---|
| 15 | Exhibit and Financial Statement Schedules |
| 16 | Form 10-K Summary (optional) |

### Notes on Reserved / optional / incorporated items
- **Item 6 is `[Reserved]`** in the current form (formerly "Selected Financial Data," eliminated 2021). Live-verified in the form PDF. The pipeline should expect Item 6 to be absent or a one-line placeholder in recent filings — but present with content in pre-2021 filings.
- **Item 16 (Form 10-K Summary) is at the registrant's option** — "Registrants may, at their option, include a summary… if each item is presented fairly and accurately with hyperlinks." Frequently **absent**. ([Form 10-K instructions](https://www.sec.gov/files/form10-k_1.pdf))
- **Item 1C (Cybersecurity)** was added by the SEC's final rule adopted **July 26, 2023**, directing registrants to new **Item 106 of Regulation S-K**. Required beginning with **annual reports for fiscal years ending on or after December 15, 2023** (smaller reporting companies' incident-disclosure piece phased later). **Filings before FY2023 have no Item 1C.** ([WilmerHale](https://www.wilmerhale.com/en/insights/blogs/keeping-current-disclosure-and-governance-developments/20230728-sec-adopts-cybersecurity-disclosure-rules); [Deloitte DART](https://dart.deloitte.com/USDART/home/publications/deloitte/heads-up/2023/sec-rule-cyber-disclosures))
- **Part III (Items 10–14) is routinely incorporated by reference** from the definitive proxy statement (DEF 14A), filed within 120 days of fiscal year-end, per General Instruction G(3). When incorporated, the 10-K body contains only a **pointer sentence** ("The information required by this Item is incorporated by reference from the Registrant's definitive Proxy Statement…"), not the content. **A pipeline that expects substantive Part III text will find near-empty items for most large filers.** The form PDF live-confirms: "Part III (Items 10, 11, 12, 13 and 14) may be incorporated by reference from the registrant's… definitive proxy statement." ([Form 10-K, General Instruction G](https://www.sec.gov/files/form10-k_1.pdf))

---

## 4. Real Sources of Format Variance That Break Naive Parsers

These are empirically grounded (live filings + practitioner reports), and are the reason a pure-regex segmenter plateaus around the low-90s F1 (per the academic literature in our memory).

1. **`Item 1` regex over-matches `Item 10–16`.** Searching for `Item 1` also hits `Item 10`, `Item 11`, `Item 12`… A naive parser grabs the *last* `Item 1` match (which is actually inside Item 12) and mislocates the boundary. Standard workaround: anchor with word/sentence boundaries and require the trailing period/title, or select the `Item 1` occurrence that precedes the first `Item 1A`. ([yuzhu.run: how to parse 10-X](https://yuzhu.run/how-to-parse-10x/); [Posit Community: rm_between regex](https://forum.posit.co/t/parsing-parts-of-10-k-reports-with-rm-between-regex/148340))
2. **Item titles appear multiple times** — once in the table of contents, once as the real header, and again as cross-references ("see Item 7"). The first/last match is often the TOC or a reference, not the section start. ([How to parse 10-K, gist](https://gist.github.com/anshoomehra/ead8925ea291e233a5aa2dcaa2dc61b2))
3. **Header-string variants for the same item:** `Item 1.`, `ITEM 1`, `Item&#160;1` / `Item 1` (non-breaking space, very common in HTML era), `ITEM&nbsp;1.`, bold/styled `<span>Item</span> <span>1</span>` split across tags, `Item 1 –` vs `Item 1.`, em-dash vs hyphen, extra whitespace. The header text can be fragmented across multiple HTML elements so the literal string never appears in extracted plain text. ([SRAF parsing docs](https://sraf.nd.edu/sec-edgar-data/cleaned-10x-files/10x-stage-one-parsing-documentation/); live `&#160;` observed)
4. **TOC anchors present vs absent.** Some filings have `<a href="#item1">` HTML anchors you can follow deterministically; many do not, forcing text-pattern fallback. No guarantee either way.
5. **Items split across pages / interleaved.** A section can be interrupted by page-break artifacts, repeated running headers/footers, or (in pathological filings) physically reordered — e.g. part of Item 8 placed after Item 15 (a documented hard case). Item boundaries are not guaranteed monotonic in file order.
6. **Exhibit index (Item 15) noise.** The exhibit list and exhibit files repeat form/item language and `EX-` types; a greedy parser can bleed Item 15 into the exhibits or vice-versa.
7. **Smaller Reporting Companies (SRCs) legitimately omit items.** SRCs may use **scaled disclosure**: they **may omit Item 7A** (Quantitative/Qualitative Market Risk, Item 305) and provide only **2 years** of financials instead of 3. So a "missing" item is sometimes correct, not a parse failure — the pipeline must distinguish *absent-by-rule* from *missed-by-parser*. ([SEC: Smaller Reporting Companies](https://www.sec.gov/resources-small-businesses/going-public/smaller-reporting-companies); [Lexology: SRC scaled disclosure](https://www.lexology.com/library/detail.aspx?g=03f8d227-80bc-4ca1-96be-df46d640f34b))
8. **Era-dependent item set/titles** (see §2.2): pre-2021 filings have a content-bearing Item 6; pre-FY2023 have no Item 1C; pre-2001 use different Item 4/6/14 titles entirely. The expected-item template must be **keyed to filing date**.
9. **Encoding/entity noise** (`&#8217;` smart quotes, `&#8212;` em-dash, `##TABLE_START`-style markers from some commercial parsers) must be normalized before matching. ([from our segmentation memory; sec-api.io behavior])

---

## Implications for Our Pipeline

1. **Access layer — do it correctly once.** Set a descriptive `User-Agent` (name + email) on every request and a global ≤10 req/s rate limiter with backoff on HTTP 429/`Request Rate Threshold Exceeded`. Do not rely on WebFetch-style clients — they are 403'd. For corpus-scale runs, prefer the nightly **bulk ZIPs** and **quarterly full-index** files over per-filing API hits.
2. **Canonical resolution path:** ticker → `company_tickers.json` → CIK (zero-pad to 10) → `data.sec.gov/submissions/CIK##########.json` → pick `form=="10-K"` index → build archive URL from `accessionNumber` (no-dash) + `primaryDocument`. Follow `filings.files[]` for deep history. This is verified and deterministic.
3. **Parse the primary `.htm` for narrative items**, not the R-files. R-files/`FilingSummary.xml`/`companyfacts` give XBRL financial facts — use those as an **independent ground-truth check on the Item 8 boundary** (a tagged revenue/asset fact must fall inside Item 8), never as the source of Item 1–7 prose. This is a zero-labeling-cost validator.
4. **Branch by era.** Detect filing date (from the SGML header or submissions metadata) and select the correct expected-item template: pre-2001 plaintext (strip PEM wrapper, all-caps headers, legacy titles), 2001–2009 HTML, post-iXBRL. Don't assume today's titles/numbering.
5. **Header matching must be variant-tolerant:** normalize entities/whitespace/NBSP first; match `Item\s*<num>` with boundary + trailing title/period; disambiguate Item 1 vs 10–16; prefer following HTML TOC anchors when present, fall back to text patterns when not; skip TOC and cross-reference occurrences (the header is usually not the first match).
6. **Missing ≠ broken.** Encode the rules: Item 6 `[Reserved]` post-2021; Item 16 optional; Item 1C only FY2023+; Part III (10–14) usually incorporated-by-reference (pointer only); SRCs may omit Item 7A and run 2-year financials. Flag absences against the *rule-appropriate* template, not a fixed 1–16 set.
7. **Pre-2001 is full-text-search-blind.** EFTS only indexes 2001+. For older filings, discovery must go through the quarterly indexes / submissions API, not full-text search.
8. **Expect a long tail.** Naive regex tops out around low-90s F1 (per our segmentation literature). Layer cheap structural parsing on the ~95% well-formed filings and reserve expensive (LLM/line-ID) methods for the ambiguous minority, with structural invariants (monotonic ordering, non-overlapping coverage, round-trip reconstruction) as the confidence signal.

---

## Sources

- [SEC: EDGAR Application Programming Interfaces (APIs)](https://www.sec.gov/search-filings/edgar-application-programming-interfaces)
- [SEC: Accessing EDGAR Data (rate limit, User-Agent, archives, indexes)](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data)
- [SEC: Developer Resources](https://www.sec.gov/about/developer-resources)
- [SEC: New rate control limits announcement](https://www.sec.gov/filergroup/announcements-old/new-rate-control-limits)
- [SEC: EDGAR Full-Text Search](https://www.sec.gov/edgar/search/) and [EFTS FAQ (since-2001 coverage, query syntax)](https://www.sec.gov/edgar/search/efts-faq.html)
- [SEC: Inline XBRL](https://www.sec.gov/data-research/structured-data/inline-xbrl)
- [SEC: Form 10-K (official PDF, item titles/instructions)](https://www.sec.gov/files/form10-k_1.pdf)
- [SEC: Regulation S-K (17 CFR 229) C&DIs](https://www.sec.gov/rules-regulations/staff-guidance/compliance-disclosure-interpretations/regulation-s-k)
- [SEC: Smaller Reporting Companies (scaled disclosure)](https://www.sec.gov/resources-small-businesses/going-public/smaller-reporting-companies)
- Live probes (2026-06-22): [Apple submissions JSON](https://data.sec.gov/submissions/CIK0000320193.json), [Apple 2025 10-K primary iXBRL doc](https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm), [Apple 2025 filing index.json](https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/index.json), [Apple complete submission .txt](https://www.sec.gov/Archives/edgar/data/320193/0000320193-25-000079.txt), [Microsoft FY1998 plaintext 10-K](https://www.sec.gov/Archives/edgar/data/789019/0001032210-98-001067.txt), EFTS JSON API `efts.sec.gov/LATEST/search-index`
- [WilmerHale: SEC adopts cybersecurity disclosure rules (Item 1C / Item 106)](https://www.wilmerhale.com/en/insights/blogs/keeping-current-disclosure-and-governance-developments/20230728-sec-adopts-cybersecurity-disclosure-rules)
- [Deloitte DART: SEC cyber disclosure effective dates](https://dart.deloitte.com/USDART/home/publications/deloitte/heads-up/2023/sec-rule-cyber-disclosures)
- [Lexology: Smaller Reporting Companies scaled disclosure](https://www.lexology.com/library/detail.aspx?g=03f8d227-80bc-4ca1-96be-df46d640f34b)
- [SRAF / Notre Dame: 10-X Stage-One Parsing documentation](https://sraf.nd.edu/sec-edgar-data/cleaned-10x-files/10x-stage-one-parsing-documentation/)
- [yuzhu.run: How to parse 10-K and 10-Q](https://yuzhu.run/how-to-parse-10x/) ; [GitHub gist: How to parse 10-K from EDGAR](https://gist.github.com/anshoomehra/ead8925ea291e233a5aa2dcaa2dc61b2) ; [Posit Community: rm_between regex pitfalls](https://forum.posit.co/t/parsing-parts-of-10-k-reports-with-rm-between-regex/148340)
- [tldrfiling: EDGAR Full-Text Search API guide](https://tldrfiling.com/blog/sec-edgar-full-text-search-api) ; [sec-api.io: extract financial statements / R-files](https://sec-api.io/resources/extract-financial-statements-from-sec-filings-and-xbrl-data-with-python)
