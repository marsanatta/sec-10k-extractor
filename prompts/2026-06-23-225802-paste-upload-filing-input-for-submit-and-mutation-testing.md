# Paste/Upload Filing Input — For "Submit A Filing" And Interactive Mutation Testing

- **Datetime:** 2026-06-23 22:58:02 (Asia/Taipei, UTC+8)
- **Summary:** The user pointed out that mutation testing (validate-the-validator) needs a way to feed a *modified* filing into the tool, and that this is the same mechanism as "upload a filing." Design that input type. Also fix the buried access-token UX so a human naturally fills the token before a custom lookup.

## Prompt

> but then how about we want to do mutating test? it then requires this tool to have some alternative to use the mutated test input. i feel the upload and also this input way is similar you can design for it (i mean design this type of input) /save-prompt

(Preceding context: I had argued upload was not strictly required by ASSIGNMENT.md because ticker/accession already lets reviewers test any real 10-K on EDGAR. The mutation-testing rationale changed my answer — a paste/upload input is the natural vehicle for it.)

## What I Did

- **Conceded the point honestly:** a paste/upload text input unifies three needs with one mechanism (`extract_from_text`, no network): (a) literal "submit a filing", (b) HTML upload, (c) **mutated-test input** — paste a filing, delete/reorder/truncate an Item, watch the validation layer react. Aligns with the assignment's "verify yourself without public ground truth."
- **Backend** (`api/server.py`): `POST /api/extract-text {text}` runs the offline pipeline. HTML is stripped via BeautifulSoup (already a dep) and normalised through the same `to_canonical` path so offsets/segmentation match an EDGAR fetch. 6MB cap (413); empty -> 400. It sits under the `/api/extract` path prefix, so the existing token-gate middleware covers it automatically (user-supplied compute on a public URL needs the shared token). Tests: gate-401, empty-400, and a real **offline** run (no monkeypatch) asserting segmentation works without network.
- **Frontend UX redesign** (`InputBar.tsx` + `styles.css`): replaced the single row (token buried after the button) with two visually distinct groups — **"Curated demo (no token)"** and a bordered **"Look up or submit a filing (needs access token)"** group with the token field FIRST (labelled "(required)" until filled), a **Ticker / Accession / Paste-upload** mode switch, an amber `needs-token` highlight on the group, and Extract disabled with an inline prompt until the token is present. Paste mode has a textarea + a `.txt/.htm` file picker (FileReader -> textarea). `api.ts` `extractText()`, `App.tsx` `runText()`.
- **Verified end-to-end in real Docker via the public tunnel:** rebuilt the stack; `/api/extract-text` returns 401 without (and with a wrong) token; the offline path runs; and a **truncation mutation on a clean filing (KO) flipped needs_review False->True** (coverage 0.981 -> 0.963, 3 items -> extraction_failure) — the validate-the-validator demo, live. RCA noted: an initial mutation attempt used M2i (degenerate: regex already finds 0 items, no signal) and a header-delete regex that hit the TOC line rather than the body anchor — switched to KO + truncation for a clear signal.
- Full suite **55 passed**; `npm run build` + 15 vitest green. Committed (no secrets in diff, neutral author). Did NOT push. Stack left running so the user can keep testing.

## Note
Open follow-ups for the full assignment submission remain: root README + analysis report, and a long-lived public deployment (the quick-tunnel URL is per-session). A fresh independent code-review of this security-touching change is available on request.
