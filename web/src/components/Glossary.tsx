import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import type { GlossaryKey } from "../i18n";

const GROUPS = [
  {
    heading: "howItWorks.toggle",
    terms: ["indexDontGenerate", "calibratedConfidence", "tabInspect", "tabEval"],
  },
  {
    heading: "summary.title",
    terms: [
      "coverage",
      "needsReview",
      "item8Xbrl",
      "roundTrip",
      "structural",
      "boundaryDisagreement",
      "escalation",
      "escalationTokens",
      "formatEra",
    ],
  },
  {
    heading: "detail.provenance",
    terms: [
      "present",
      "absent",
      "failure",
      "confHigh",
      "confMedium",
      "confLow",
      "confUnscored",
      "provenance",
      "checks",
      "charRange",
      "boundaryViewer",
    ],
  },
  {
    heading: "input.customTitle",
    terms: ["curatedDemo", "accessToken", "ticker", "accession", "pasteUpload"],
  },
] as const satisfies { heading: string; terms: readonly GlossaryKey[] }[];

export function Glossary() {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const closeRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (open) closeRef.current?.focus();
  }, [open]);

  return (
    <>
      <button type="button" className="glossary-open" onClick={() => setOpen(true)}>
        {t("glossary.title")}
      </button>
      {open && (
        <div
          className="glossary-overlay"
          onClick={() => setOpen(false)}
          onKeyDown={(e) => e.key === "Escape" && setOpen(false)}
          role="presentation"
        >
          <div
            className="glossary-dialog"
            role="dialog"
            aria-modal="true"
            aria-label={t("glossary.title")}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="glossary-head">
              <h2>{t("glossary.title")}</h2>
              <button
                type="button"
                ref={closeRef}
                className="glossary-close"
                aria-label="Close"
                onClick={() => setOpen(false)}
              >
                ✕
              </button>
            </div>
            <p className="glossary-intro">{t("glossary.intro")}</p>
            {GROUPS.map((group) => (
              <section key={group.heading} className="glossary-group">
                <h3>{t(group.heading)}</h3>
                <dl>
                  {group.terms.map((term) => (
                    <div className="glossary-row" key={term}>
                      <dt>{t(`g.${term}.t`)}</dt>
                      <dd>{t(`g.${term}.d`)}</dd>
                    </div>
                  ))}
                </dl>
              </section>
            ))}
          </div>
        </div>
      )}
    </>
  );
}
