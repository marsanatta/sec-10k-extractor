import { useEffect, useRef } from "react";
import { useTranslation } from "react-i18next";
import { sliceAroundRange } from "../lib/format";
import type { Item } from "../types";

interface Props {
  canonicalText: string;
  item: Item;
}

export function BoundaryViewer({ canonicalText, item }: Props) {
  const { t } = useTranslation();
  const markRef = useRef<HTMLElement>(null);
  const slice = sliceAroundRange(canonicalText, item.char_range);

  useEffect(() => {
    markRef.current?.scrollIntoView({ block: "center" });
  }, [item.item_id]);

  if (!item.char_range) {
    return <div className="empty">{t("detail.noSourceSpan")}</div>;
  }

  return (
    <div className="boundary" aria-label={t("boundary.ariaLabel")}>
      {slice.truncatedHead && (
        <span className="truncation">{t("boundary.earlierOmitted")}{"\n"}</span>
      )}
      <span>{slice.before}</span>
      <mark ref={markRef}>{slice.highlight}</mark>
      {slice.highlightOmitted > 0 && (
        <>
          <span className="truncation">
            {t("boundary.highlightElided", { count: slice.highlightOmitted.toLocaleString() })}
          </span>
          <mark>{slice.highlightTail}</mark>
        </>
      )}
      <span>{slice.after}</span>
      {slice.truncatedTail && (
        <span className="truncation">{"\n"}{t("boundary.laterOmitted")}</span>
      )}
    </div>
  );
}
