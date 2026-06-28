import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { extract, extractDemo, extractText, fetchDemos, fetchModels } from "./api";
import { ExampleGallery } from "./components/ExampleGallery";
import { FailureInspector } from "./components/FailureInspector";
import { InfoTip } from "./components/InfoTip";
import { InputBar } from "./components/InputBar";
import { ItemDetail } from "./components/ItemDetail";
import { ItemNavigator } from "./components/ItemNavigator";
import { LanguageSwitcher } from "./components/LanguageSwitcher";
import { Onboarding } from "./components/Onboarding";
import { SummaryPanel } from "./components/SummaryPanel";
import type { DemoEntry, ExtractRequest, ExtractionResult, Item, ModelInfo } from "./types";

export default function App() {
  const { t } = useTranslation();
  const [demos, setDemos] = useState<DemoEntry[]>([]);
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [defaultModel, setDefaultModel] = useState("");
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
    fetchModels()
      .then((r) => {
        setModels(r.models);
        setDefaultModel(r.default);
      })
      .catch(() => undefined);
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
  const runText = (text: string, model?: string, escalate?: boolean) =>
    run(() => extractText(text, token, model, escalate));

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">{t("app.title")}</div>
        <div className="topbar-actions">
          <Onboarding hasResult={result != null} onLoadExample={() => runDemo("msft-fy1995")} />
          <LanguageSwitcher />
        </div>
      </header>

      <div className="workspace">
        <aside className="examples-sidebar" data-tour="demo">
          <div className="sidebar-head">
            <span className="sidebar-title">{t("input.demoTitle")}</span>
            <InfoTip term="curatedDemo" />
            <small>{t("input.demoNote")}</small>
          </div>
          <ExampleGallery demos={demos} loading={loading} onDemo={runDemo} />
        </aside>

        <main className="workmain">
          <InputBar
            models={models}
            defaultModel={defaultModel}
            loading={loading}
            elapsed={elapsed}
            onSubmit={runExtract}
            onText={runText}
            token={token}
            onToken={setToken}
          />
          {error && <div className="error">{error}</div>}

          {result && (
            <p className="meta-line" data-tour="meta">
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
        </main>
      </div>
    </div>
  );
}
