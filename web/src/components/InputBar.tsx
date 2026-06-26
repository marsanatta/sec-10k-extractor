import { Fragment, useState } from "react";
import { useTranslation } from "react-i18next";
import type { GlossaryKey } from "../i18n";
import type { DemoEntry, ExtractRequest } from "../types";
import { InfoTip } from "./InfoTip";

type Mode = "ticker" | "accession" | "text";

const MODE_LABEL = {
  ticker: "input.modeTicker",
  accession: "input.modeAccession",
  text: "input.modeText",
} as const;

const MODE_TERM: Record<Mode, GlossaryKey> = {
  ticker: "ticker",
  accession: "accession",
  text: "pasteUpload",
};

interface Props {
  demos: DemoEntry[];
  loading: boolean;
  elapsed: number;
  onSubmit: (req: ExtractRequest) => void;
  onDemo: (id: string) => void;
  onText: (text: string) => void;
  token: string;
  onToken: (value: string) => void;
}

export function InputBar({
  demos,
  loading,
  elapsed,
  onSubmit,
  onDemo,
  onText,
  token,
  onToken,
}: Props) {
  const { t } = useTranslation();
  const [demo, setDemo] = useState("");
  const [mode, setMode] = useState<Mode>("ticker");
  const [ticker, setTicker] = useState("");
  const [fiscalYear, setFiscalYear] = useState("");
  const [accession, setAccession] = useState("");
  const [text, setText] = useState("");
  const [fileError, setFileError] = useState("");

  const input =
    mode === "ticker" ? ticker.trim() : mode === "accession" ? accession.trim() : text.trim();
  const hasInput = Boolean(input);
  const hasToken = Boolean(token.trim());
  const canSubmit = hasInput && hasToken && !loading;

  function pickDemo(id: string) {
    const entry = demos.find((d) => d.id === id);
    if (!entry) return;
    setDemo("");
    onDemo(entry.id);
  }

  function submit() {
    if (!canSubmit) return;
    if (mode === "ticker") {
      onSubmit({
        ticker: ticker.trim().toUpperCase(),
        fiscal_year: fiscalYear ? Number(fiscalYear) : undefined,
      });
    } else if (mode === "accession") {
      onSubmit({ accession: accession.trim() });
    } else {
      onText(text);
    }
  }

  function loadFile(file: File | undefined) {
    if (!file) return;
    if (file.size > 24_000_000) {
      setFileError(t("input.fileTooLarge"));
      return;
    }
    setFileError("");
    const reader = new FileReader();
    reader.onerror = () => setFileError(t("input.fileReadError"));
    reader.onload = () => {
      setText(String(reader.result ?? ""));
      setMode("text");
    };
    reader.readAsText(file);
  }

  return (
    <div className="inputbar">
      <div className="lookup-group demo-group" data-tour="demo">
        <span className="group-title">
          {t("input.demoTitle")}
          <InfoTip term="curatedDemo" />
          <small>· {t("input.demoNote")}</small>
        </span>
        <select
          value={demo}
          disabled={loading}
          onChange={(e) => {
            setDemo(e.target.value);
            if (e.target.value) pickDemo(e.target.value);
          }}
        >
          <option value="">{t("input.demoPlaceholder")}</option>
          {demos.map((d) => (
            <option key={d.id} value={d.id}>
              {d.label} — {d.note}
            </option>
          ))}
        </select>
      </div>

      <div
        className={`lookup-group custom-group${hasInput && !hasToken ? " needs-token" : ""}`}
        data-tour="lookup"
      >
        <span className="group-title">
          {t("input.customTitle")}
          <small>· {t("input.customNote")}</small>
        </span>

        <div className="field token-field">
          <span className="field-label-row">
            <label htmlFor="token">
              {t("input.tokenLabel")}
              {hasToken ? "" : ` ${t("input.tokenRequired")}`}
            </label>
            <InfoTip term="accessToken" />
          </span>
          <input
            id="token"
            type="password"
            placeholder={t("input.tokenPlaceholder")}
            value={token}
            disabled={loading}
            autoComplete="off"
            onChange={(e) => onToken(e.target.value)}
          />
        </div>

        <div className="mode-switch" role="tablist">
          {(["ticker", "accession", "text"] as Mode[]).map((m) => (
            <Fragment key={m}>
              <button
                role="tab"
                aria-selected={mode === m}
                className={`mode-tab${mode === m ? " active" : ""}`}
                disabled={loading}
                onClick={() => setMode(m)}
              >
                {t(MODE_LABEL[m])}
              </button>
              <InfoTip term={MODE_TERM[m]} />
            </Fragment>
          ))}
        </div>

        {mode === "ticker" && (
          <div className="mode-fields">
            <input
              placeholder={t("input.tickerPlaceholder")}
              value={ticker}
              disabled={loading}
              onChange={(e) => setTicker(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && submit()}
            />
            <input
              placeholder={t("input.fiscalYearPlaceholder")}
              inputMode="numeric"
              value={fiscalYear}
              disabled={loading}
              onChange={(e) => setFiscalYear(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && submit()}
            />
          </div>
        )}
        {mode === "accession" && (
          <div className="mode-fields">
            <input
              placeholder={t("input.accessionPlaceholder")}
              value={accession}
              disabled={loading}
              onChange={(e) => setAccession(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && submit()}
            />
          </div>
        )}
        {mode === "text" && (
          <div className="mode-fields text-mode">
            <textarea
              placeholder={t("input.textPlaceholder")}
              value={text}
              disabled={loading}
              rows={4}
              onChange={(e) => setText(e.target.value)}
            />
            <label className="file-btn">
              {t("input.uploadButton")}
              <input
                type="file"
                accept=".txt,.htm,.html,.sgml"
                disabled={loading}
                onChange={(e) => loadFile(e.target.files?.[0])}
                hidden
              />
            </label>
            {fileError && <span className="hint">{fileError}</span>}
          </div>
        )}

        <button className="btn-primary" disabled={!canSubmit} onClick={submit}>
          {loading ? t("input.extracting") : t("input.extract")}
        </button>
        {hasInput && !hasToken && <span className="hint">{t("input.needTokenHint")}</span>}
      </div>

      {loading && (
        <span className="elapsed">
          <span className="spinner" aria-hidden="true" />
          {t("input.elapsed", { seconds: elapsed })}
        </span>
      )}
    </div>
  );
}
