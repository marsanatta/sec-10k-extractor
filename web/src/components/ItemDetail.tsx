import { useState } from "react";
import { useTranslation } from "react-i18next";
import { itemColor } from "../lib/format";
import type { Item } from "../types";
import { BoundaryViewer } from "./BoundaryViewer";
import { InfoTip } from "./InfoTip";

interface Props {
  item: Item;
  canonicalText: string;
}

/** A provenance check tag (e.g. "boundary_xcheck") with a hover tooltip that educates what it
 *  means. Falls back to the raw tag for any tag without an i18n entry, so a new production tag
 *  never crashes or shows blank. */
function ProvenanceChip({ tag, ok }: { tag: string; ok: boolean }) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const label = t(`prov.${tag}.t`, { defaultValue: tag });
  const desc = t(`prov.${tag}.d`, { defaultValue: "" });
  return (
    <span
      className={`chip ${ok ? "pass" : "fail"} tagtip`}
      tabIndex={0}
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
      onFocus={() => setOpen(true)}
      onBlur={() => setOpen(false)}
    >
      {ok ? "✓" : "✕"} {tag}
      {open && desc && (
        <span role="tooltip" className="infotip-bubble">
          <strong>{label}</strong>
          <span>{desc}</span>
        </span>
      )}
    </span>
  );
}

export function ItemDetail({ item, canonicalText }: Props) {
  const { t } = useTranslation();
  const color = itemColor(item);
  const score = item.confidence.score;
  return (
    <section className="panel detail" aria-label={t("detail.itemKey", { item: item.item })}>
      <h1>
        <span className="item-key">{t("detail.itemKey", { item: item.item })}</span> — {item.title}
      </h1>
      <div className="badges" data-tour="badges">
        <span className={`badge ${color}`}>
          {t(`status.${item.status}`)}
          <InfoTip
            term={
              item.status === "present"
                ? "present"
                : item.status === "legitimately_absent"
                  ? "absent"
                  : "failure"
            }
          />
        </span>
        {item.status === "present" && (
          <span className={`badge ${color}`}>
            {t(`band.${item.confidence.band}`)}
            {score != null && ` (${score.toFixed(2)})`}
            <InfoTip
              term={
                item.confidence.band === "high"
                  ? "confHigh"
                  : item.confidence.band === "medium"
                    ? "confMedium"
                    : item.confidence.band === "low"
                      ? "confLow"
                      : "confUnscored"
              }
            />
          </span>
        )}
        {item.char_range && (
          <span className="badge">
            {t("detail.chars", {
              start: item.char_range[0].toLocaleString(),
              end: item.char_range[1].toLocaleString(),
            })}
            <InfoTip term="charRange" />
          </span>
        )}
      </div>

      <p className="subhead">
        {t("detail.provenance")}
        <InfoTip term="provenance" />
      </p>
      <div className="chips" data-tour="provenance">
        {item.provenance.checks_passed.map((c) => (
          <ProvenanceChip key={`p-${c}`} tag={c} ok={true} />
        ))}
        {item.provenance.checks_failed.map((c) => (
          <ProvenanceChip key={`f-${c}`} tag={c} ok={false} />
        ))}
        {item.provenance.checks_passed.length === 0 &&
          item.provenance.checks_failed.length === 0 && (
            <span className="chip">{t("detail.noChecks")}</span>
          )}
      </div>

      {item.status === "present" ? (
        <>
          <p className="subhead">
            {t("detail.boundaryViewer")}
            <InfoTip term="boundaryViewer" />
          </p>
          <BoundaryViewer canonicalText={canonicalText} item={item} />
          <p className="subhead">{t("detail.extractedText")}</p>
          <div className="item-text">{item.text || t("detail.emptyText")}</div>
        </>
      ) : (
        <p className="empty">
          {item.status === "legitimately_absent"
            ? t("detail.absentExplain")
            : t("detail.failureExplain")}
        </p>
      )}
    </section>
  );
}
