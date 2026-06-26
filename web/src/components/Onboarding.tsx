import { useEffect, useRef } from "react";
import { useTranslation } from "react-i18next";
import { hasSeenTour, markTourSeen, resumeAfterLoad, startTour } from "../onboarding";

interface Props {
  hasResult: boolean;
  onLoadExample: () => void;
}

export function Onboarding({ hasResult, onLoadExample }: Props) {
  const { t } = useTranslation();
  const autoStarted = useRef(false);

  useEffect(() => {
    if (autoStarted.current || hasSeenTour()) return;
    autoStarted.current = true;
    const id = requestAnimationFrame(() => {
      startTour(t, hasResult, onLoadExample);
      markTourSeen();
    });
    return () => cancelAnimationFrame(id);
  }, [t, hasResult, onLoadExample]);

  useEffect(() => {
    if (!hasResult) return;
    const id = requestAnimationFrame(() => resumeAfterLoad());
    return () => cancelAnimationFrame(id);
  }, [hasResult]);

  return (
    <button
      type="button"
      className="tour-replay"
      onClick={() => startTour(t, hasResult, onLoadExample)}
    >
      {t("onboarding.replay")}
    </button>
  );
}
