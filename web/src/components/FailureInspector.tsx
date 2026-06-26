import { useTranslation } from "react-i18next";
import type { Item } from "../types";
import { InfoTip } from "./InfoTip";

interface Props {
  items: Item[];
  onSelect: (item: Item) => void;
}

export function FailureInspector({ items, onSelect }: Props) {
  const { t } = useTranslation();
  const failures = items.filter((it) => it.status === "extraction_failure");
  const absent = items.filter((it) => it.status === "legitimately_absent");

  return (
    <aside className="panel" aria-label={t("failures.title")}>
      <h2>{t("failures.title")}</h2>

      <div className="failure-group">
        <h3 style={{ color: "var(--red)" }}>
          {t("failures.failuresHead", { count: failures.length })}
          <InfoTip term="failure" />
        </h3>
        {failures.length === 0 ? (
          <p className="empty">{t("failures.noFailures")}</p>
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
        <h3 style={{ color: "var(--text-faint)" }}>
          {t("failures.absentHead", { count: absent.length })}
          <InfoTip term="absent" />
        </h3>
        {absent.map((it) => (
          <div className="failure-item" key={it.item_id}>
            <span className="fkey">{t("detail.itemKey", { item: it.item })}</span> —{" "}
            {it.confidence.signals[0] ?? t("failures.absentFallback")}
          </div>
        ))}
      </div>
    </aside>
  );
}
