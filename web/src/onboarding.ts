import { driver, type DriveStep } from "driver.js";
import "driver.js/dist/driver.css";
import type { TFunction } from "i18next";

const TOUR_KEY = "sec10k_onboarded_v1";
const ONE_YEAR = 60 * 60 * 24 * 365;

export function hasSeenTour(): boolean {
  return document.cookie.split("; ").some((c) => c === `${TOUR_KEY}=1`);
}

export function markTourSeen(): void {
  document.cookie = `${TOUR_KEY}=1; max-age=${ONE_YEAR}; path=/; SameSite=Lax`;
}

const STEPS = [
  { key: "welcome", element: undefined },
  { key: "tagline", element: '[data-tour="tagline"]' },
  { key: "demo", element: '[data-tour="demo"]' },
  { key: "lookup", element: '[data-tour="lookup"]' },
  { key: "tabs", element: '[data-tour="tabs"]' },
  { key: "lang", element: '[data-tour="lang"]' },
] as const;

function steps(t: TFunction): DriveStep[] {
  return STEPS.map((s) => ({
    element: s.element,
    popover: {
      title: t(`onboarding.${s.key}Title`),
      description: t(`onboarding.${s.key}Body`),
    },
  }));
}

export function startTour(t: TFunction): void {
  driver({
    showProgress: true,
    allowClose: true,
    popoverClass: "sec10k-tour",
    progressText: t("onboarding.progress"),
    nextBtnText: t("onboarding.next"),
    prevBtnText: t("onboarding.back"),
    doneBtnText: t("onboarding.done"),
    steps: steps(t),
  }).drive();
}
