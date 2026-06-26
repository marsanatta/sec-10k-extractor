import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";
import type { TFunction } from "i18next";
import type { GlossaryKey } from "../i18n";
import type { Summary } from "../types";
import { InfoTip } from "./InfoTip";

interface Props {
  summary: Summary;
}

function reviewDrivers(s: Summary, t: TFunction): string[] {
  const drivers: string[] = [];
  if (s.structural_ok === false) drivers.push(t("summary.driverStructural"));
  if (s.round_trip_ok === false) drivers.push(t("summary.driverRoundTrip"));
  if (s.coverage_plausible === false)
    drivers.push(t("summary.driverCoverage", { percent: (s.coverage_fraction * 100).toFixed(0) }));
  if (s.items_extraction_failure > 0)
    drivers.push(t("summary.driverFailures", { count: s.items_extraction_failure }));
  if (s.low_confidence_items > 0)
    drivers.push(t("summary.driverLowConf", { count: s.low_confidence_items }));
  if (s.item8_markers === false) drivers.push(t("summary.driverItem8"));
  if (s.boundary_disagreements.length > 0)
    drivers.push(t("summary.driverBoundary", { items: s.boundary_disagreements.join(", ") }));
  return drivers;
}

function Row({ k, term, v }: { k: string; term?: GlossaryKey; v: ReactNode }) {
  return (
    <div className="summary-row">
      <span className="k">
        {k}
        {term && <InfoTip term={term} />}
      </span>
      <span className="v">{v}</span>
    </div>
  );
}

export function SummaryPanel({ summary: s }: Props) {
  const { t } = useTranslation();
  const drivers = reviewDrivers(s, t);
  return (
    <aside className="panel" aria-label={t("summary.title")} data-tour="summary">
      <h2>{t("summary.title")}</h2>
      <div className={`review-banner ${s.needs_review ? "flag" : "clean"}`}>
        <span className="banner-label">
          {s.needs_review ? t("summary.needsReview") : t("summary.noFlags")}
          <InfoTip term="needsReview" />
        </span>
        {s.needs_review && drivers.length > 0 && (
          <ul className="drivers">
            {drivers.map((d) => (
              <li key={d}>{d}</li>
            ))}
          </ul>
        )}
      </div>

      <Row
        k={t("summary.coverage")}
        term="coverage"
        v={`${(s.coverage_fraction * 100).toFixed(1)}%`}
      />
      <Row k={t("summary.present")} term="present" v={s.items_present} />
      <Row k={t("summary.absent")} term="absent" v={s.items_legitimately_absent} />
      <Row k={t("summary.failures")} term="failure" v={s.items_extraction_failure} />
      <Row
        k={t("summary.lowMedConf")}
        term="calibratedConfidence"
        v={`${s.low_confidence_items} / ${s.medium_confidence_items}`}
      />
      <Row
        k={t("summary.item8Oracle")}
        term="item8Xbrl"
        v={
          s.item8_xbrl_checked > 0
            ? t("summary.item8Found", { found: s.item8_xbrl_found, checked: s.item8_xbrl_checked })
            : s.item8_markers == null
              ? t("summary.item8Na")
              : s.item8_markers
                ? t("summary.item8MarkersPresent")
                : t("summary.item8MarkersAbsent")
        }
      />
      <Row
        k={t("summary.boundaryDisagreements")}
        term="boundaryDisagreement"
        v={s.boundary_disagreements.length ? s.boundary_disagreements.join(", ") : t("summary.none")}
      />
      <Row k={t("summary.formatEra")} term="formatEra" v={s.format_era} />

      <p className="subhead">
        {t("summary.escalationHead")}
        <InfoTip term="escalation" />
      </p>
      <Row k={t("summary.provider")} v={s.escalation_provider} />
      <Row
        k={t("summary.performed")}
        v={
          s.escalation_performed
            ? t("summary.performedYes")
            : t("summary.performedNo", { provider: s.escalation_provider })
        }
      />
      <Row
        k={t("summary.candidates")}
        v={s.escalation_candidates.length ? s.escalation_candidates.join(", ") : t("summary.none")}
      />
      <Row
        k={t("summary.calls")}
        term="escalationTokens"
        v={s.escalation_performed ? s.escalation_calls : t("summary.callsNone")}
      />
      <Row
        k={t("summary.tokens")}
        v={
          s.escalation_performed
            ? `${s.escalation_input_tokens.toLocaleString()} / ${s.escalation_output_tokens.toLocaleString()}`
            : t("summary.tokensNone")
        }
      />
    </aside>
  );
}
