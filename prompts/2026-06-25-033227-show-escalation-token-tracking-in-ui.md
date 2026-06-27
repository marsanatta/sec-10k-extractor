# Show Escalation Token Tracking In The UI Frontend

- **Datetime:** 2026-06-25 03:32:27
- **Summary:** Check whether the new escalation token tracking surfaces in the web UI; if not, design it from our frontend skills and run /eng-pipe to add the token display.

## Prompt

> will those token track show in UI frontend? if not, search frontend skills we have design it, and /eng-pipe to add them /save-prompt

## What I Did

- Answered the factual question first, with evidence from the code:
  - **API already exposes the data.** `api/server.py` returns `asdict(result)`, so the full
    `summary` — including the new `escalation_calls` / `escalation_input_tokens` /
    `escalation_output_tokens` — is in the browser payload. No backend change needed.
  - **Frontend gap.** `web/src/types.ts` `Summary` omits the 3 new token fields, and
    `web/src/components/SummaryPanel.tsx` renders only Provider / Performed / Candidates in its
    "Escalation (LLM tier)" subsection — calls and tokens are not shown.
  - Conclusion: token tracking does NOT show in the UI; it is a frontend-only gap.
- Saved this prompt (Taipei time per project convention) — this record.
- Ran `/eng-pipe` to add the measured token ledger (calls + input/output tokens) to the existing
  Escalation subsection of `SummaryPanel.tsx`, with honest "0 — not exercised (deferred)" framing,
  plus the `Summary` type fields. (See the eng-pipe run + commit for the implementation detail.)
