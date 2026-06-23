import type { Item } from "../types";

interface Props {
  items: Item[];
  onSelect: (item: Item) => void;
}

export function FailureInspector({ items, onSelect }: Props) {
  const failures = items.filter((it) => it.status === "extraction_failure");
  const absent = items.filter((it) => it.status === "legitimately_absent");

  return (
    <aside className="panel" aria-label="Failure inspector">
      <h2>Missing items</h2>

      <div className="failure-group">
        <h3 style={{ color: "var(--red)" }}>Extraction failures ({failures.length})</h3>
        {failures.length === 0 ? (
          <p className="empty">None — every expected item was found.</p>
        ) : (
          failures.map((it) => (
            <button key={it.item_id} className="nav-item" onClick={() => onSelect(it)}>
              <span className="dot red" aria-hidden="true" />
              <span className="key">{it.item}</span>
              <span className="nav-title">{it.title}</span>
            </button>
          ))
        )}
      </div>

      <div className="failure-group">
        <h3 style={{ color: "var(--text-faint)" }}>Legitimately absent ({absent.length})</h3>
        {absent.map((it) => (
          <div className="failure-item" key={it.item_id}>
            <span className="fkey">Item {it.item}</span> — {it.confidence.signals[0] ?? "absent"}
          </div>
        ))}
      </div>
    </aside>
  );
}
