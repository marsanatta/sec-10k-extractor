import { useTranslation } from "react-i18next";
import { LANG_KEY, type AppLang } from "../i18n";

export function LanguageSwitcher() {
  const { i18n, t } = useTranslation();
  const current: AppLang = i18n.language === "en" ? "en" : "zh-Hant";

  function set(lng: AppLang) {
    i18n.changeLanguage(lng);
    localStorage.setItem(LANG_KEY, lng);
  }

  return (
    <div className="lang-switch" role="group" aria-label={t("lang.ariaSwitch")} data-tour="lang">
      <button
        type="button"
        className={`lang-btn${current === "en" ? " active" : ""}`}
        aria-pressed={current === "en"}
        onClick={() => set("en")}
      >
        {t("lang.toEnglish")}
      </button>
      <button
        type="button"
        className={`lang-btn${current === "zh-Hant" ? " active" : ""}`}
        aria-pressed={current === "zh-Hant"}
        onClick={() => set("zh-Hant")}
      >
        {t("lang.toChinese")}
      </button>
    </div>
  );
}
