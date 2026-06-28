import { driver, type Config, type DriveStep } from "driver.js";
import "driver.js/dist/driver.css";
import type { TFunction } from "i18next";

const TOUR_KEY = "sec10k_tour_v1";
const ONE_YEAR = 60 * 60 * 24 * 365;

function hasCookie(key: string): boolean {
  return document.cookie.split("; ").some((c) => c === `${key}=1`);
}

function setCookie(key: string): void {
  document.cookie = `${key}=1; max-age=${ONE_YEAR}; path=/; SameSite=Lax`;
}

export const hasSeenTour = () => hasCookie(TOUR_KEY);
export const markTourSeen = () => setCookie(TOUR_KEY);

const INPUT_STEPS = [
  { key: "welcome", element: undefined },
  { key: "demo", element: '[data-tour="demo"]' },
  { key: "lookup", element: '[data-tour="lookup"]' },
  { key: "lang", element: '[data-tour="lang"]' },
] as const;

const REPORT_STEPS = [
  { key: "meta", element: '[data-tour="meta"]' },
  { key: "nav", element: '[data-tour="navigator"]' },
  { key: "detail", element: '[data-tour="badges"]' },
  { key: "boundary", element: '[data-tour="boundary"]' },
  { key: "prov", element: '[data-tour="provenance"]' },
  { key: "summary", element: '[data-tour="summary"]' },
  { key: "failures", element: '[data-tour="failures"]' },
] as const;

const REPORT_ANCHOR = '[data-tour="meta"]';

type StepKey = (typeof INPUT_STEPS)[number]["key"] | (typeof REPORT_STEPS)[number]["key"];

function toSteps(table: readonly { key: StepKey; element?: string }[], t: TFunction): DriveStep[] {
  return table.map((s) => ({
    element: s.element,
    popover: {
      title: t(`onboarding.${s.key}Title`),
      description: t(`onboarding.${s.key}Body`),
    },
  }));
}

let active: ReturnType<typeof driver> | null = null;
let awaitingResult = false;

function bridgeStep(t: TFunction, onLoadExample: () => void): DriveStep {
  return {
    element: undefined,
    popover: {
      title: t("onboarding.loadExampleTitle"),
      description: t("onboarding.loadExampleBody"),
      onNextClick: () => {
        if (!active) return;
        // A report is already on screen (replay, or user re-entered this step) -> just continue.
        if (document.querySelector(REPORT_ANCHOR)) {
          active.moveNext();
          return;
        }
        onLoadExample();
        awaitingResult = true; // resumed by resumeAfterLoad() once the result renders
      },
    },
  };
}

export function startTour(t: TFunction, hasResult: boolean, onLoadExample: () => void): void {
  active?.destroy();
  awaitingResult = false;
  const steps = hasResult
    ? [...toSteps(INPUT_STEPS, t), ...toSteps(REPORT_STEPS, t)]
    : [...toSteps(INPUT_STEPS, t), bridgeStep(t, onLoadExample), ...toSteps(REPORT_STEPS, t)];
  const config: Config = {
    showProgress: true,
    allowClose: true,
    popoverClass: "sec10k-tour",
    progressText: t("onboarding.progress"),
    nextBtnText: t("onboarding.next"),
    prevBtnText: t("onboarding.back"),
    doneBtnText: t("onboarding.done"),
    steps,
    onDestroyed: () => {
      active = null;
      awaitingResult = false;
    },
  };
  active = driver(config);
  active.drive();
}

// Called when an extraction result has rendered; advances a tour paused on the bridge step.
export function resumeAfterLoad(): void {
  if (active && awaitingResult) {
    awaitingResult = false;
    active.moveNext();
  }
}
