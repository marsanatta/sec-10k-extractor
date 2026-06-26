import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { extract, extractDemo, extractText, fetchDemos } from "./api";
import { EvalView } from "./components/EvalView";
import { FailureInspector } from "./components/FailureInspector";
import { InfoTip } from "./components/InfoTip";
import { InputBar } from "./components/InputBar";
import { ItemDetail } from "./components/ItemDetail";
import { ItemNavigator } from "./components/ItemNavigator";
import { LanguageSwitcher } from "./components/LanguageSwitcher";
import { Onboarding } from "./components/Onboarding";
import { SummaryPanel } from "./components/SummaryPanel";
import type { DemoEntry, ExtractRequest, ExtractionResult, Item } from "./types";

type Tab = "inspect" | "eval";

export default function App() {
  const { t } = useTranslation();
  const [tab, setTab] = useState<Tab>("inspect");
  const [demos, setDemos] = useState<DemoEntry[]>([]);
  const [result, setResult] = useState<ExtractionResult | null>(null);
  const [selected, setSelected] = useState<Item | null>(null);
  const [loading, setLoading] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [token, setToken] = useState(() => localStorage.getItem("sec10k_access_token") ?? "");
  const timer = useRef<number | null>(null);

  useEffect(() => {
    localStorage.setItem("sec10k_access_token", token);
  }, [token]);

  useEffect(() => {
    fetchDemos()
      .then(setDemos)
      .catch((e: Error) => setError(e.message));
  }, []);

  async function run(fetcher: () => Promise<ExtractionResult>) {
    setLoading(true);
    setError(null);
    setElapsed(0);
    const started = Date.now();
    timer.current = window.setInterval(
      () => setElapsed(Math.round((Date.now() - started) / 1000)),
      1000,
    );
    try {
      const res = await fetcher();
      setResult(res);
      const firstPresent = res.items.find((it) => it.status === "present") ?? res.items[0] ?? null;
      setSelected(firstPresent);
    } catch (e) {
      setError((e as Error).message);
      setResult(null);
      setSelected(null);
    } finally {
      if (timer.current) window.clearInterval(timer.current);
      setLoading(false);
    }
  }

  const runExtract = (req: ExtractRequest) => run(() => extract(req, token));
  const runDemo = (id: string) => run(() => extractDemo(id));
  const runText = (text: string) => run(() => extractText(text, token));

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          {t("app.title")}
          <small data-tour="tagline">
            {t("app.taglineIndex")}
            <InfoTip term="indexDontGenerate" /> · {t("app.taglineConfidence")}
            <InfoTip term="calibratedConfidence" />
          </small>
        </div>
        <div className="topbar-actions">
          <Onboarding />
          <LanguageSwitcher />
        </div>
        <div className="tabs" data-tour="tabs">
          <button
            className="tab"
            aria-pressed={tab === "inspect"}
            onClick={() => setTab("inspect")}
          >
            {t("tabs.inspect")}
          </button>
          <InfoTip term="tabInspect" />
          <button className="tab" aria-pressed={tab === "eval"} onClick={() => setTab("eval")}>
            {t("tabs.eval")}
          </button>
          <InfoTip term="tabEval" />
        </div>
      </header>

      {tab === "eval" ? (
        <EvalView />
      ) : (
        <>
          <InputBar
            demos={demos}
            loading={loading}
            elapsed={elapsed}
            onSubmit={runExtract}
            onDemo={runDemo}
            onText={runText}
            token={token}
            onToken={setToken}
          />
          {error && <div className="error">{error}</div>}

          {result && (
            <p className="meta-line">
              <strong>{result.meta.company || t("meta.unknownFiler")}</strong> · {result.meta.form}{" "}
              · {t("meta.fy")}
              {result.meta.fiscal_year ?? "?"} · {t("meta.filed")} {result.meta.filing_date || "?"}{" "}
              · <span className="mono">{result.meta.accession}</span> · {t("meta.era")}{" "}
              {result.meta.format_era}
            </p>
          )}

          {result ? (
            <div className="layout">
              <ItemNavigator
                items={result.items}
                selectedId={selected?.item_id ?? null}
                onSelect={setSelected}
              />
              {selected ? (
                <ItemDetail item={selected} canonicalText={result.canonical_text} />
              ) : (
                <div className="panel empty">{t("empty.selectItem")}</div>
              )}
              <div>
                <SummaryPanel summary={result.summary} />
                <div style={{ height: 16 }} />
                <FailureInspector items={result.items} onSelect={setSelected} />
              </div>
            </div>
          ) : (
            !loading && <div className="empty">{t("empty.start")}</div>
          )}
        </>
      )}
    </div>
  );
}
