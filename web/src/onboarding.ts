import { driver, type Config, type DriveStep } from "driver.js";
import "driver.js/dist/driver.css";
import type { TFunction } from "i18next";

const INPUT_KEY = "sec10k_onboarded_v1";
const REPORT_KEY = "sec10k_report_tour_v1";
const ONE_YEAR = 60 * 60 * 24 * 365;

function hasCookie(key: string): boolean {
  return document.cookie.split("; ").some((c) => c === `${key}=1`);
}

function setCookie(key: string): void {
  document.cookie = `${key}=1; max-age=${ONE_YEAR}; path=/; SameSite=Lax`;
}

export const hasSeenInputTour = () => hasCookie(INPUT_KEY);
export const markInputTourSeen = () => setCookie(INPUT_KEY);
export const hasSeenReportTour = () => hasCookie(REPORT_KEY);
export const markReportTourSeen = () => setCookie(REPORT_KEY);

const INPUT_STEPS = [
  { key: "welcome", element: undefined },
  { key: "tagline", element: '[data-tour="tagline"]' },
  { key: "demo", element: '[data-tour="demo"]' },
  { key: "lookup", element: '[data-tour="lookup"]' },
  { key: "tabs", element: '[data-tour="tabs"]' },
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

type StepKey =
  | (typeof INPUT_STEPS)[number]["key"]
  | (typeof REPORT_STEPS)[number]["key"];

function toSteps(
  table: readonly { key: StepKey; element?: string }[],
  t: TFunction,
): DriveStep[] {
  return table.map((s) => ({
    element: s.element,
    popover: {
      title: t(`onboarding.${s.key}Title`),
      description: t(`onboarding.${s.key}Body`),
    },
  }));
}

let active: ReturnType<typeof driver> | null = null;

function run(steps: DriveStep[], t: TFunction): void {
  active?.destroy();
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
    },
  };
  active = driver(config);
  active.drive();
}

export function startInputTour(t: TFunction): void {
  run(toSteps(INPUT_STEPS, t), t);
}

export function startReportTour(t: TFunction): void {
  run(toSteps(REPORT_STEPS, t), t);
}

export function startFullTour(t: TFunction, hasResult: boolean): void {
  const table = hasResult ? [...INPUT_STEPS, ...REPORT_STEPS] : INPUT_STEPS;
  run(toSteps(table, t), t);
}
