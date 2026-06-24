# edgar-corpus three-way cross-check (SPIKE)

Run: 2026-06-24 23:35 Asia/Taipei. On-demand (HF download) -- NOT the CI gate. A third DECORRELATED boundary
signal (edgar-corpus, independent toolkit) vs our correlated regex+edgartools. It is
lossy + text-only + 1993-2020, so located starts are APPROXIMATE; it does NOT replace the
5 human-audited char-exact gold filings (still the floor) and is NOT frozen into gold.

- Item-boundaries where all three agree (<250 chars): **3/9** -> high confidence (the common-mode was NOT lying there)
- Item-boundaries where edgar-corpus DISAGREES with the regex+edgartools consensus: **0** -> flag for human audit

| filing | item | our_start | edgartools_start | edgar-corpus_start | spread | 3-way agree | flag |
|---|---|---|---|---|---|---|---|
| msft-fy1995 | 1 | 5646 | None | 5646 | 0 | False |  |
| msft-fy1995 | 1A | None | None | None | None | False |  |
| msft-fy1995 | 7 | 60724 | None | 60724 | 0 | False |  |
| ge-fy2009 | 1 | 5327 | 5327 | 5327 | 0 | True |  |
| ge-fy2009 | 1A | 53097 | 53097 | 53097 | 0 | True |  |
| ge-fy2009 | 7 | 97060 | 97060 | 97060 | 0 | True |  |
| xom-fy2010 | 1 | 9379 | 117219 | 9379 | 107840 | False |  |
| xom-fy2010 | 1A | 15491 | None | None | None | False |  |
| xom-fy2010 | 7 | 112180 | 173205 | None | 61025 | False |  |
