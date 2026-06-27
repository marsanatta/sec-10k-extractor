"""MEASURE whether the real Copilot LLM escalation tier earns its keep -- before round-3 assumes it.

REPORTED-only, independent-reference-only. Never edits/freezes any gold; scores LLM-on vs LLM-off
against the FROZEN human gold (Signal B = char-exact boundary IoU; Signal D = classification match),
never against the LLM's own confidence. On-demand (network + a Copilot token for the LLM-on arm).

Run:  GH_TOKEN=$(gh auth token) SEC_EDGAR_USER_AGENT="Name email" python eval/llm_measure.py
Writes eval/llm_measure_results.json (gitignored). The narrative verdict is hand-written into
research/llm-measurement-findings.md from these numbers.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sec10k.boundary_crosscheck import edgartools_item_texts
from sec10k.escalation import DeferredLLMClient, build_lib_prompt, run_escalation
from sec10k.evalkit import boundary_scores, classification_match_rate
from sec10k.ingest import fetch_10k
from sec10k.normalize import to_canonical
from sec10k.pipeline import _build_result, extract_from_text
from sec10k.schema import Band, Status

HERE = Path(__file__).parent
EVAL_SET = json.loads((HERE / "eval_set.json").read_text())["filings"]
BGOLD = json.loads((HERE / "boundary_gold.json").read_text())
CGOLD = json.loads((HERE / "classification_gold.json").read_text()).get("filings", {})


def _real_client():
    from sec10k.copilot_client import CopilotLLMClient

    return CopilotLLMClient()


def _present_low_conf(result) -> list[dict]:
    """The items the apply-loop can ACTUALLY fire on: present, not-HIGH, with a char_range to move.
    (extraction_failures are escalation_candidates too, but have no char_range -> never called.)"""
    out = []
    for it in result.items:
        if it.status == Status.PRESENT and it.confidence.band != Band.HIGH and it.char_range:
            out.append({"item": it.item, "band": it.confidence.band.value})
    return out


def _signals(result, gid):
    b = boundary_scores(result, BGOLD[gid]["items"]) if gid in BGOLD else None
    d = (classification_match_rate(result, CGOLD[gid]["labels"]) if gid in CGOLD else None)
    return b, d


def measure_filing(entry: dict) -> dict:
    gid, acc = entry["id"], entry["accession"]
    raw = fetch_10k(accession=acc)
    canonical, era = to_canonical(raw)
    second = edgartools_item_texts(raw.accession)

    off = _build_result(canonical, era, raw, llm_client=DeferredLLMClient(), second_text=second)
    s_off = off.summary
    eligible = _present_low_conf(off)
    cands = s_off.get("escalation_candidates") or []
    b_off, d_off = _signals(off, gid)

    rec = {
        "id": gid, "accession": acc, "era": era, "form": off.meta.form,
        "is_boundary_gold": gid in BGOLD, "is_class_gold": gid in CGOLD,
        "n_candidates": len(cands), "candidates": cands,
        "n_actual_call_eligible": len(eligible), "actual_call_eligible": eligible,
        "extraction_failures": [it.item for it in off.items if it.status == Status.EXTRACTION_FAILURE],
        "boundary_off": b_off, "classification_off": d_off,
    }

    # LLM-on arm only where the LLM can actually do something (eligible) or where gold can score it.
    if eligible or gid in BGOLD or gid in CGOLD:
        on = _build_result(canonical, era, raw, llm_client=_real_client(), second_text=second)
        s_on = on.summary
        b_on, d_on = _signals(on, gid)
        rec.update({
            "llm_provider": s_on.get("escalation_provider"),
            "llm_touched": s_on.get("llm_touched"),
            "llm_calls": s_on.get("escalation_calls"),
            "llm_applied": s_on.get("escalation_applied"),
            "llm_items_moved": s_on.get("escalation_items_moved"),
            "llm_input_tokens": s_on.get("escalation_input_tokens"),
            "llm_output_tokens": s_on.get("escalation_output_tokens"),
            "boundary_on": b_on, "classification_on": d_on,
            "boundary_delta": (round((b_on["mean_iou"] or 0) - (b_off["mean_iou"] or 0), 4)
                               if b_off and b_on else None),
            "classification_delta": (round((d_on["match_rate"] or 0) - (d_off["match_rate"] or 0), 4)
                                     if d_off and d_on else None),
        })
    return rec


DOC = (
    "TABLE OF CONTENTS\nItem 1. Business 3\nItem 3. Legal 9\n"
    "PART I\nItem 1. Business\n" + "We make and sell products worldwide. " * 30 + "\n"
    "Item 3. Legal Proceedings\n" + "Various legal matters are pending. " * 30 + "\n"
)


def mechanism_real_model() -> dict:
    """Non-tautological end-to-end proof: inject a deliberately-WRONG boundary on a present item,
    let the REAL model adjudicate, and check the span moves back to the known-correct start. The
    reference (true_start) is independent of the LLM; LLM-off leaves it wrong (proven by the
    offline deferred-ledger tests). Fails if the real model + apply-loop don't work."""
    result = extract_from_text(DOC, fiscal_year=2024)
    canonical = result.canonical_text
    it = next(i for i in result.items if i.status == Status.PRESENT and i.char_range)
    true_start, end = it.char_range
    wrong_start = true_start + 40
    it.char_range = (wrong_start, end)
    it.text = canonical[wrong_start:end]
    it.confidence.band = Band.MEDIUM

    prompt = build_lib_prompt(canonical, it.item, wrong_start)
    client = _real_client()
    raw_answer = client.adjudicate(prompt)
    out = run_escalation(result, canonical, client)
    moved_to = it.char_range[0]
    return {
        "model": client.name,
        "item": it.item,
        "true_start": true_start, "wrong_start": wrong_start, "moved_to": moved_to,
        "real_model_raw_answer": (raw_answer.text if raw_answer else None),
        "applied": out["escalation_applied"],
        "fixed": moved_to == true_start,
    }


def main() -> int:
    rows = []
    for i, entry in enumerate(EVAL_SET, 1):
        try:
            rec = measure_filing(entry)
        except Exception as exc:  # network/parse failures must not abort the whole measurement
            rec = {"id": entry["id"], "accession": entry["accession"], "error": f"{type(exc).__name__}: {exc}"}
        rows.append(rec)
        c = rec.get("n_candidates", "ERR")
        e = rec.get("n_actual_call_eligible", "?")
        moved = rec.get("llm_items_moved")
        print(f"[{i}/{len(EVAL_SET)}] {entry['id']:<20} cand={c} eligible={e} moved={moved}",
              file=sys.stderr, flush=True)

    print("[mechanism] real-model one-shot...", file=sys.stderr, flush=True)
    try:
        mech = mechanism_real_model()
    except Exception as exc:
        mech = {"error": f"{type(exc).__name__}: {exc}"}
    print(f"[mechanism] {mech}", file=sys.stderr, flush=True)

    ok = [r for r in rows if "error" not in r]
    triggers = [r for r in ok if r["n_candidates"] > 0]
    eligible = [r for r in ok if r["n_actual_call_eligible"] > 0]
    gold_triggers = [r for r in ok if (r["is_boundary_gold"] or r["is_class_gold"]) and r["n_actual_call_eligible"] > 0]
    out = {
        "n_measured": len(ok), "n_errors": len(rows) - len(ok),
        "trigger_rate": f"{len(triggers)}/{len(ok)}",
        "actual_call_rate": f"{len(eligible)}/{len(ok)}",
        "gold_filings_with_actual_calls": [r["id"] for r in gold_triggers],
        "mechanism_real_model": mech,
        "rows": rows,
    }
    (HERE / "llm_measure_results.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if k != "rows"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
