import { useEffect, useRef } from "react";
import { sliceAroundRange } from "../lib/format";
import type { Item } from "../types";

interface Props {
  canonicalText: string;
  item: Item;
}

export function BoundaryViewer({ canonicalText, item }: Props) {
  const markRef = useRef<HTMLElement>(null);
  const slice = sliceAroundRange(canonicalText, item.char_range);

  useEffect(() => {
    markRef.current?.scrollIntoView({ block: "center" });
  }, [item.item_id]);

  if (!item.char_range) {
    return (
      <div className="empty">
        No source span for this item (not present in the document).
      </div>
    );
  }

  return (
    <div className="boundary" aria-label="Source text with item boundary highlighted">
      {slice.truncatedHead && <span className="truncation">…[earlier text omitted]…{"\n"}</span>}
      <span>{slice.before}</span>
      <mark ref={markRef}>{slice.highlight}</mark>
      <span>{slice.after}</span>
      {slice.truncatedTail && <span className="truncation">{"\n"}…[later text omitted]…</span>}
    </div>
  );
}
