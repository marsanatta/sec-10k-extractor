import { useEffect } from "react";
import { useTranslation } from "react-i18next";
import {
  hasSeenInputTour,
  hasSeenReportTour,
  markInputTourSeen,
  markReportTourSeen,
  startFullTour,
  startInputTour,
  startReportTour,
} from "../onboarding";

interface Props {
  hasResult: boolean;
}

export function Onboarding({ hasResult }: Props) {
  const { t } = useTranslation();

  useEffect(() => {
    if (hasSeenInputTour()) return;
    const id = requestAnimationFrame(() => {
      startInputTour(t);
      markInputTourSeen();
    });
    return () => cancelAnimationFrame(id);
  }, [t]);

  useEffect(() => {
    if (!hasResult || hasSeenReportTour()) return;
    const id = requestAnimationFrame(() => {
      startReportTour(t);
      markReportTourSeen();
    });
    return () => cancelAnimationFrame(id);
  }, [hasResult, t]);

  return (
    <button type="button" className="tour-replay" onClick={() => startFullTour(t, hasResult)}>
      {t("onboarding.replay")}
    </button>
  );
}
