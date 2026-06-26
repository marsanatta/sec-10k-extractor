import { useState } from "react";
import { useTranslation } from "react-i18next";

export function HowItWorks() {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);

  return (
    <div className="how">
      <button
        type="button"
        className="how-toggle"
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
      >
        {open ? "▾" : "▸"} {t("howItWorks.toggle")}
      </button>
      {open && (
        <section className="how-panel" aria-label={t("howItWorks.ariaRegion")}>
          <p className="how-intro">{t("howItWorks.intro")}</p>
          <ol className="how-steps">
            {(["step1", "step2", "step3", "step4"] as const).map((s) => (
              <li key={s}>
                <span className="how-step-title">{t(`howItWorks.${s}Title`)}</span>
                <span className="how-step-body">{t(`howItWorks.${s}Body`)}</span>
              </li>
            ))}
          </ol>
        </section>
      )}
    </div>
  );
}
