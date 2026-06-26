import { useTranslation } from "react-i18next";
import { itemColor } from "../lib/format";
import type { Item } from "../types";
import { BoundaryViewer } from "./BoundaryViewer";
import { InfoTip } from "./InfoTip";

interface Props {
  item: Item;
  canonicalText: string;
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
      <div className="badges">
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
