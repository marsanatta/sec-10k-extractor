import { bandLabel, itemColor, statusLabel } from "../lib/format";
import type { Item } from "../types";
import { BoundaryViewer } from "./BoundaryViewer";

interface Props {
  item: Item;
  canonicalText: string;
}

export function ItemDetail({ item, canonicalText }: Props) {
  const color = itemColor(item);
  const score = item.confidence.score;
  return (
    <section className="panel detail" aria-label="Item detail">
      <h1>
        <span className="item-key">Item {item.item}</span> — {item.title}
      </h1>
      <div className="badges">
        <span className={`badge ${color}`}>{statusLabel(item.status)}</span>
        {item.status === "present" && (
          <span className={`badge ${color}`}>
            {bandLabel(item.confidence.band)}
            {score != null && ` (${score.toFixed(2)})`}
          </span>
        )}
        {item.char_range && (
          <span className="badge">
            chars {item.char_range[0].toLocaleString()}–{item.char_range[1].toLocaleString()}
          </span>
        )}
      </div>

      <p className="subhead">Provenance</p>
      <div className="chips">
        {item.provenance.checks_passed.map((c) => (
          <span className="chip pass" key={`p-${c}`}>
            ✓ {c}
          </span>
        ))}
        {item.provenance.checks_failed.map((c) => (
          <span className="chip fail" key={`f-${c}`}>
            ✕ {c}
          </span>
        ))}
        {item.provenance.checks_passed.length === 0 &&
          item.provenance.checks_failed.length === 0 && (
            <span className="chip">no checks recorded</span>
          )}
      </div>

      {item.status === "present" ? (
        <>
          <p className="subhead">Boundary viewer (source span highlighted)</p>
          <BoundaryViewer canonicalText={canonicalText} item={item} />
          <p className="subhead">Extracted text</p>
          <div className="item-text">{item.text || "(empty)"}</div>
        </>
      ) : (
        <p className="empty">
          {item.status === "legitimately_absent"
            ? "This item is legitimately absent for this filing (template/DEI says optional, reserved, or incorporated by reference)."
            : "This item was expected but not found — a flagged extraction failure, not a silent drop."}
        </p>
      )}
    </section>
  );
}
