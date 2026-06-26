import { useId, useState } from "react";
import { useTranslation } from "react-i18next";
import type { GlossaryKey } from "../i18n";

interface Props {
  term: GlossaryKey;
}

export function InfoTip({ term }: Props) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const id = useId();
  const title = t(`g.${term}.t`);
  const body = t(`g.${term}.d`);

  return (
    <span className="infotip">
      <button
        type="button"
        className="infotip-trigger"
        aria-label={title}
        aria-describedby={open ? id : undefined}
        aria-expanded={open}
        onMouseEnter={() => setOpen(true)}
        onMouseLeave={() => setOpen(false)}
        onFocus={() => setOpen(true)}
        onBlur={() => setOpen(false)}
        onClick={() => setOpen((v) => !v)}
        onKeyDown={(e) => e.key === "Escape" && setOpen(false)}
      >
        ⓘ
      </button>
      {open && (
        <span role="tooltip" id={id} className="infotip-bubble">
          <strong>{title}</strong>
          <span>{body}</span>
        </span>
      )}
    </span>
  );
}
