import type { ReactNode } from "react";
import type { Summary } from "../types";

interface Props {
  summary: Summary;
}

function reviewDrivers(s: Summary): string[] {
  const drivers: string[] = [];
  if (s.structural_ok === false) drivers.push("structural invariants broken");
  if (s.round_trip_ok === false) drivers.push("round-trip reconstruction failed");
  if (s.coverage_plausible === false)
    drivers.push(`coverage implausibly low (${(s.coverage_fraction * 100).toFixed(0)}%)`);
  if (s.items_extraction_failure > 0)
    drivers.push(`${s.items_extraction_failure} expected item(s) not found`);
  if (s.low_confidence_items > 0) drivers.push(`${s.low_confidence_items} low-confidence item(s)`);
  if (s.item8_markers === false) drivers.push("Item 8 financial markers absent");
  if (s.boundary_disagreements.length > 0)
    drivers.push(`boundary disagreement on ${s.boundary_disagreements.join(", ")}`);
  return drivers;
}

function Row({ k, v }: { k: string; v: ReactNode }) {
  return (
    <div className="summary-row">
      <span className="k">{k}</span>
      <span className="v">{v}</span>
    </div>
  );
}

export function SummaryPanel({ summary: s }: Props) {
  const drivers = reviewDrivers(s);
  return (
    <aside className="panel" aria-label="Filing summary">
      <h2>Filing summary</h2>
      <div className={`review-banner ${s.needs_review ? "flag" : "clean"}`}>
        {s.needs_review ? "Needs review" : "No review flags"}
        {s.needs_review && drivers.length > 0 && (
          <ul className="drivers">
            {drivers.map((d) => (
              <li key={d}>{d}</li>
            ))}
          </ul>
        )}
      </div>

      <Row k="Coverage" v={`${(s.coverage_fraction * 100).toFixed(1)}%`} />
      <Row k="Present" v={s.items_present} />
      <Row k="Legitimately absent" v={s.items_legitimately_absent} />
      <Row k="Extraction failures" v={s.items_extraction_failure} />
      <Row k="Low / medium conf." v={`${s.low_confidence_items} / ${s.medium_confidence_items}`} />
      <Row
        k="Item 8 XBRL oracle"
        v={
          s.item8_xbrl_checked > 0
            ? `${s.item8_xbrl_found}/${s.item8_xbrl_checked} found`
            : s.item8_markers == null
              ? "n/a"
              : s.item8_markers
                ? "markers present"
                : "markers absent"
        }
      />
      <Row
        k="Boundary disagreements"
        v={s.boundary_disagreements.length ? s.boundary_disagreements.join(", ") : "none"}
      />
      <Row k="Format era" v={s.format_era} />

      <p className="subhead">Escalation (LLM tier)</p>
      <Row k="Provider" v={s.escalation_provider} />
      <Row
        k="Performed"
        v={
          s.escalation_performed
            ? "yes"
            : `no — ${s.escalation_provider} stub (deferred)`
        }
      />
      <Row
        k="Candidates"
        v={s.escalation_candidates.length ? s.escalation_candidates.join(", ") : "none"}
      />
      <Row
        k="Calls"
        v={s.escalation_performed ? s.escalation_calls : "0 — not exercised (deferred)"}
      />
      <Row
        k="Tokens (in / out)"
        v={
          s.escalation_performed
            ? `${s.escalation_input_tokens.toLocaleString()} / ${s.escalation_output_tokens.toLocaleString()}`
            : "0 / 0 — measured, no LLM call"
        }
      />
    </aside>
  );
}
