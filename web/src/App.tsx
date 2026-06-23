import { useEffect, useRef, useState } from "react";
import { extract, fetchDemos } from "./api";
import { EvalView } from "./components/EvalView";
import { FailureInspector } from "./components/FailureInspector";
import { InputBar } from "./components/InputBar";
import { ItemDetail } from "./components/ItemDetail";
import { ItemNavigator } from "./components/ItemNavigator";
import { SummaryPanel } from "./components/SummaryPanel";
import type { DemoEntry, ExtractRequest, ExtractionResult, Item } from "./types";

type Tab = "inspect" | "eval";

export default function App() {
  const [tab, setTab] = useState<Tab>("inspect");
  const [demos, setDemos] = useState<DemoEntry[]>([]);
  const [result, setResult] = useState<ExtractionResult | null>(null);
  const [selected, setSelected] = useState<Item | null>(null);
  const [loading, setLoading] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const timer = useRef<number | null>(null);

  useEffect(() => {
    fetchDemos()
      .then(setDemos)
      .catch((e: Error) => setError(e.message));
  }, []);

  async function runExtract(req: ExtractRequest) {
    setLoading(true);
    setError(null);
    setElapsed(0);
    const started = Date.now();
    timer.current = window.setInterval(
      () => setElapsed(Math.round((Date.now() - started) / 1000)),
      1000,
    );
    try {
      const res = await extract(req);
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

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          SEC 10-K Item Extractor
          <small>index-don't-generate · calibrated confidence</small>
        </div>
        <div className="tabs">
          <button
            className="tab"
            aria-pressed={tab === "inspect"}
            onClick={() => setTab("inspect")}
          >
            Inspect
          </button>
          <button className="tab" aria-pressed={tab === "eval"} onClick={() => setTab("eval")}>
            Eval / still-hard
          </button>
        </div>
      </header>

      {tab === "eval" ? (
        <EvalView />
      ) : (
        <>
          <InputBar demos={demos} loading={loading} elapsed={elapsed} onSubmit={runExtract} />
          {error && <div className="error">{error}</div>}

          {result && (
            <p className="meta-line">
              <strong>{result.meta.company || "(unknown filer)"}</strong> · {result.meta.form} ·
              FY{result.meta.fiscal_year ?? "?"} · filed {result.meta.filing_date || "?"} ·{" "}
              <span className="mono">{result.meta.accession}</span> · era{" "}
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
                <div className="panel empty">Select an item to inspect.</div>
              )}
              <div>
                <SummaryPanel summary={result.summary} />
                <div style={{ height: 16 }} />
                <FailureInspector items={result.items} onSelect={setSelected} />
              </div>
            </div>
          ) : (
            !loading && (
              <div className="empty">
                Pick a curated demo, or enter a ticker + fiscal year or an EDGAR accession, then
                Extract. Results are cached by accession.
              </div>
            )
          )}
        </>
      )}
    </div>
  );
}
