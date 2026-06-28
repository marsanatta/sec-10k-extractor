import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import en from "./locales/en.json";
import zhHant from "./locales/zh-Hant.json";

export const defaultNS = "translation";
export const LANG_KEY = "sec10k_lng";

export const resources = {
  en: { translation: en },
  "zh-Hant": { translation: zhHant },
} as const;

export type AppLang = keyof typeof resources;
export type GlossaryKey = keyof typeof en.g;
export type DemoKey = keyof typeof en.demos;

i18n.use(initReactI18next).init({
  resources,
  lng: localStorage.getItem(LANG_KEY) ?? "zh-Hant",
  fallbackLng: "en",
  defaultNS,
  interpolation: { escapeValue: false },
});

export default i18n;
