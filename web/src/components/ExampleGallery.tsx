import { useState } from "react";
import { useTranslation } from "react-i18next";
import type { DemoKey } from "../i18n";
import type { DemoEntry } from "../types";

interface Props {
  demos: DemoEntry[];
  loading: boolean;
  onDemo: (id: string) => void;
}

const GROUP_ORDER = ["good", "limitation"] as const;

const GROUP_TITLE = {
  good: "input.groupGood",
  limitation: "input.groupLimitation",
} as const;

export function ExampleGallery({ demos, loading, onDemo }: Props) {
  const { t } = useTranslation();
  const [group, setGroup] = useState<(typeof GROUP_ORDER)[number]>("good");
  const entries = demos.filter((d) => d.group === group);

  return (
    <div className="example-gallery">
      <div className="gallery-seg" role="tablist" aria-label={t("input.demoTitle")}>
        {GROUP_ORDER.map((g) => {
          const count = demos.filter((d) => d.group === g).length;
          return (
            <button
              key={g}
              type="button"
              role="tab"
              aria-selected={group === g}
              className={`gallery-seg-btn gallery-seg-${g}${group === g ? " on" : ""}`}
              onClick={() => setGroup(g)}
            >
              {t(GROUP_TITLE[g])}
              {count > 0 && <span className="gallery-seg-count">{count}</span>}
            </button>
          );
        })}
      </div>
      <ul className={`gallery-cards gallery-${group}`}>
        {entries.map((d) => (
          <li key={d.id}>
            <button
              type="button"
              className="gallery-card"
              disabled={loading}
              onClick={() => onDemo(d.id)}
            >
              <span className="gallery-card-label">{d.label}</span>
              <span className="gallery-card-desc">{t(`demos.${d.id as DemoKey}`)}</span>
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
