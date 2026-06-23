import { useState } from "react";
import type { DemoEntry, ExtractRequest } from "../types";

interface Props {
  demos: DemoEntry[];
  loading: boolean;
  elapsed: number;
  onSubmit: (req: ExtractRequest) => void;
  token: string;
  onToken: (value: string) => void;
}

export function InputBar({ demos, loading, elapsed, onSubmit, token, onToken }: Props) {
  const [ticker, setTicker] = useState("");
  const [fiscalYear, setFiscalYear] = useState("");
  const [accession, setAccession] = useState("");
  const [demo, setDemo] = useState("");

  function submit() {
    if (accession.trim()) {
      onSubmit({ accession: accession.trim() });
    } else if (ticker.trim()) {
      onSubmit({
        ticker: ticker.trim().toUpperCase(),
        fiscal_year: fiscalYear ? Number(fiscalYear) : undefined,
      });
    }
  }

  function pickDemo(id: string) {
    const entry = demos.find((d) => d.id === id);
    if (!entry) return;
    setTicker("");
    setFiscalYear("");
    setAccession("");
    setDemo("");
    onSubmit(
      entry.accession
        ? { accession: entry.accession }
        : { ticker: entry.ticker, fiscal_year: entry.fiscal_year },
    );
  }

  return (
    <div className="inputbar">
      <div className="field">
        <label htmlFor="demo">Demo filing</label>
        <select
          id="demo"
          value={demo}
          disabled={loading}
          onChange={(e) => {
            setDemo(e.target.value);
            if (e.target.value) pickDemo(e.target.value);
          }}
        >
          <option value="">Select a curated example…</option>
          {demos.map((d) => (
            <option key={d.id} value={d.id}>
              {d.label} — {d.note}
            </option>
          ))}
        </select>
      </div>

      <span className="sep">or</span>

      <div className="field">
        <label htmlFor="ticker">Ticker</label>
        <input
          id="ticker"
          placeholder="AAPL"
          value={ticker}
          disabled={loading}
          onChange={(e) => setTicker(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && submit()}
        />
      </div>
      <div className="field">
        <label htmlFor="fy">Fiscal year</label>
        <input
          id="fy"
          placeholder="2024"
          inputMode="numeric"
          value={fiscalYear}
          disabled={loading}
          onChange={(e) => setFiscalYear(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && submit()}
        />
      </div>

      <span className="sep">or</span>

      <div className="field">
        <label htmlFor="acc">Accession</label>
        <input
          id="acc"
          placeholder="0000320193-24-000123"
          value={accession}
          disabled={loading}
          onChange={(e) => setAccession(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && submit()}
        />
      </div>

      <button
        className="btn-primary"
        disabled={loading || (!accession.trim() && !ticker.trim())}
        onClick={submit}
      >
        {loading ? "Extracting…" : "Extract"}
      </button>

      <div className="field">
        <label htmlFor="token">Access token</label>
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

      {loading && (
        <span className="elapsed">
          <span className="spinner" aria-hidden="true" />
          {elapsed}s — fetching + segmenting (a large filing can take up to ~2 min)
        </span>
      )}
    </div>
  );
}
