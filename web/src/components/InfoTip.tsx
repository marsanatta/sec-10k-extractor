import { useId, useLayoutEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import type { GlossaryKey } from "../i18n";

interface Props {
  term: GlossaryKey;
}

const EDGE_MARGIN = 8;

export function InfoTip({ term }: Props) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const [offsetX, setOffsetX] = useState(0);
  const [above, setAbove] = useState(false);
  const bubbleRef = useRef<HTMLSpanElement>(null);
  const id = useId();
  const title = t(`g.${term}.t`);
  const body = t(`g.${term}.d`);

  useLayoutEffect(() => {
    if (!open) return;

    function clamp() {
      const bubble = bubbleRef.current;
      if (!bubble) return;
      // Reset transform so the rect reflects the natural centered position before re-measuring.
      bubble.style.transform = "translateX(-50%)";
      const rect = bubble.getBoundingClientRect();
      const vw = document.documentElement.clientWidth;
      const vh = document.documentElement.clientHeight;

      let dx = 0;
      if (rect.right > vw - EDGE_MARGIN) dx = vw - EDGE_MARGIN - rect.right;
      else if (rect.left < EDGE_MARGIN) dx = EDGE_MARGIN - rect.left;

      setOffsetX(dx);
      setAbove(rect.bottom > vh - EDGE_MARGIN && rect.top - rect.height > EDGE_MARGIN);
    }

    clamp();
    window.addEventListener("resize", clamp);
    window.addEventListener("scroll", clamp, true);
    return () => {
      window.removeEventListener("resize", clamp);
      window.removeEventListener("scroll", clamp, true);
    };
  }, [open, body, title]);

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
        <span
          ref={bubbleRef}
          role="tooltip"
          id={id}
          className={`infotip-bubble${above ? " infotip-above" : ""}`}
          style={{ transform: `translateX(calc(-50% + ${offsetX}px))` }}
        >
          <strong>{title}</strong>
          <span>{body}</span>
        </span>
      )}
    </span>
  );
}
