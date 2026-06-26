import { useTranslation } from "react-i18next";
import { groupByPart, itemColor } from "../lib/format";
import type { Item } from "../types";

interface Props {
  items: Item[];
  selectedId: string | null;
  onSelect: (item: Item) => void;
}

export function ItemNavigator({ items, selectedId, onSelect }: Props) {
  const { t } = useTranslation();
  const groups = groupByPart(items);
  return (
    <nav className="panel" aria-label={t("navigator.title")} data-tour="navigator">
      <h2>{t("navigator.title")}</h2>
      {groups.map((group) => (
        <div className="nav-part" key={group.part}>
          <p className="nav-part-title">{t("navigator.part", { part: group.part })}</p>
          {group.items.map((item) => (
            <button
              key={item.item_id}
              className="nav-item"
              aria-current={item.item_id === selectedId}
              onClick={() => onSelect(item)}
            >
              <span className={`dot ${itemColor(item)}`} aria-hidden="true" />
              <span className="key">{item.item}</span>
              <span className="nav-title">{item.title}</span>
            </button>
          ))}
        </div>
      ))}
    </nav>
  );
}
