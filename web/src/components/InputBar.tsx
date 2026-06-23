import { useState } from "react";
import type { DemoEntry, ExtractRequest } from "../types";

type Mode = "ticker" | "accession" | "text";

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
  const [demo, setDemo] = useState("");
  const [mode, setMode] = useState<Mode>("ticker");
  const [ticker, setTicker] = useState("");
  const [fiscalYear, setFiscalYear] = useState("");
  const [accession, setAccession] = useState("");
  const [text, setText] = useState("");

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
    const reader = new FileReader();
    reader.onload = () => {
      setText(String(reader.result ?? ""));
      setMode("text");
    };
    reader.readAsText(file);
  }

  return (
    <div className="inputbar">
      <div className="lookup-group demo-group">
        <span className="group-title">
          Curated demo <small>· no token</small>
        </span>
        <select
          value={demo}
          disabled={loading}
          onChange={(e) => {
            setDemo(e.target.value);
            if (e.target.value) pickDemo(e.target.value);
          }}
        >
          <option value="">Pick an example…</option>
          {demos.map((d) => (
            <option key={d.id} value={d.id}>
              {d.label} — {d.note}
            </option>
          ))}
        </select>
      </div>

      <div className={`lookup-group custom-group${hasInput && !hasToken ? " needs-token" : ""}`}>
        <span className="group-title">
          Look up or submit a filing <small>· needs access token</small>
        </span>

        <div className="field token-field">
          <label htmlFor="token">Access token {hasToken ? "" : "(required)"}</label>
          <input
            id="token"
            type="password"
            placeholder="shared by the operator"
            value={token}
            disabled={loading}
            autoComplete="off"
            onChange={(e) => onToken(e.target.value)}
          />
        </div>

        <div className="mode-switch" role="tablist">
          {(["ticker", "accession", "text"] as Mode[]).map((m) => (
            <button
              key={m}
              role="tab"
              aria-selected={mode === m}
              className={`mode-tab${mode === m ? " active" : ""}`}
              disabled={loading}
              onClick={() => setMode(m)}
            >
              {m === "ticker" ? "Ticker" : m === "accession" ? "Accession" : "Paste / upload"}
            </button>
          ))}
        </div>

        {mode === "ticker" && (
          <div className="mode-fields">
            <input
              placeholder="Ticker (AAPL)"
              value={ticker}
              disabled={loading}
              onChange={(e) => setTicker(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && submit()}
            />
            <input
              placeholder="Fiscal year (2024)"
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
              placeholder="0000320193-24-000123"
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
              placeholder="Paste filing text — or copy a result's canonical text, delete/reorder an Item, and resubmit to watch the validator react…"
              value={text}
              disabled={loading}
              rows={4}
              onChange={(e) => setText(e.target.value)}
            />
            <label className="file-btn">
              Upload .txt / .htm
              <input
                type="file"
                accept=".txt,.htm,.html,.sgml"
                disabled={loading}
                onChange={(e) => loadFile(e.target.files?.[0])}
                hidden
              />
            </label>
          </div>
        )}

        <button className="btn-primary" disabled={!canSubmit} onClick={submit}>
          {loading ? "Extracting…" : "Extract"}
        </button>
        {hasInput && !hasToken && (
          <span className="hint">Enter the access token above to run this lookup.</span>
        )}
      </div>

      {loading && (
        <span className="elapsed">
          <span className="spinner" aria-hidden="true" />
          {elapsed}s — fetching + segmenting (a large filing can take up to ~2 min)
        </span>
      )}
    </div>
  );
}
