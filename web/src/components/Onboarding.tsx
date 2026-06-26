import { useEffect } from "react";
import { useTranslation } from "react-i18next";
import { hasSeenTour, markTourSeen, startTour } from "../onboarding";

export function Onboarding() {
  const { t } = useTranslation();

  useEffect(() => {
    if (hasSeenTour()) return;
    const id = requestAnimationFrame(() => {
      startTour(t);
      markTourSeen();
    });
    return () => cancelAnimationFrame(id);
  }, [t]);

  return (
    <button type="button" className="tour-replay" onClick={() => startTour(t)}>
      {t("onboarding.replay")}
    </button>
  );
}
