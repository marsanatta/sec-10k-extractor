import { useTranslation } from "react-i18next";
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

  return (
    <div className="example-gallery">
      {GROUP_ORDER.map((group) => {
        const entries = demos.filter((d) => d.group === group);
        if (entries.length === 0) return null;
        return (
          <section key={group} className={`gallery-group gallery-${group}`}>
            <h3 className="gallery-group-title">{t(GROUP_TITLE[group])}</h3>
            <ul className="gallery-cards">
              {entries.map((d) => (
                <li key={d.id}>
                  <button
                    type="button"
                    className="gallery-card"
                    disabled={loading}
                    onClick={() => onDemo(d.id)}
                  >
                    <span className="gallery-card-label">{d.label}</span>
                    <span className="gallery-card-detail">{d.detail}</span>
                  </button>
                </li>
              ))}
            </ul>
          </section>
        );
      })}
    </div>
  );
}
