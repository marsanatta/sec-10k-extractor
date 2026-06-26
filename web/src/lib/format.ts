import type { Item } from "../types";

export type StatusColor = "green" | "amber" | "red" | "muted";

/**
 * Map an item's status + confidence to a single navigator colour. Boundary disagreements
 * and low confidence are surfaced as red even when the item is present, because a wrong
 * boundary on a present item is the silent-failure mode the UI must make visible.
 */
export function itemColor(item: Item): StatusColor {
  if (item.status === "legitimately_absent") return "muted";
  if (item.status === "extraction_failure") return "red";
  const boundaryFlagged = item.provenance.checks_failed.includes("boundary_xcheck");
  if (item.confidence.band === "low" || boundaryFlagged) return "red";
  if (item.confidence.band === "medium") return "amber";
  if (item.confidence.band === "high") return "green";
  return "muted";
}

const PART_ORDER = ["I", "II", "III", "IV"];

export interface PartGroup {
  part: string;
  items: Item[];
}

export function groupByPart(items: Item[]): PartGroup[] {
  const byPart = new Map<string, Item[]>();
  for (const it of items) {
    const bucket = byPart.get(it.part);
    if (bucket) bucket.push(it);
    else byPart.set(it.part, [it]);
  }
  const known = PART_ORDER.filter((p) => byPart.has(p));
  const extra = [...byPart.keys()].filter((p) => !PART_ORDER.includes(p)).sort();
  return [...known, ...extra].map((part) => ({ part, items: byPart.get(part)! }));
}

export interface TextSlice {
  before: string;
  highlight: string;
  /** Tail of the highlighted span when it exceeds `maxHighlight` and the middle is elided. */
  highlightTail: string;
  /** Count of highlighted chars elided between `highlight` and `highlightTail` (0 if none). */
  highlightOmitted: number;
  after: string;
  /** Absolute offset where `before` starts in the source — for rendering true line/char refs. */
  sliceStart: number;
  truncatedHead: boolean;
  truncatedTail: boolean;
}

/**
 * Return a window of `text` around `range` split into before/highlight/after so the caller
 * can wrap the highlight without re-deriving offsets. When `range` is null there is nothing
 * to highlight, so the whole (head-capped) text is returned as `before`. A very large
 * highlight (e.g. Item 8 spans hundreds of KB) is elided to head+tail so the DOM stays light.
 */
export function sliceAroundRange(
  text: string,
  range: [number, number] | null,
  context = 1200,
  maxHighlight = 6000,
): TextSlice {
  if (!range) {
    const head = text.slice(0, context);
    return {
      before: head,
      highlight: "",
      highlightTail: "",
      highlightOmitted: 0,
      after: "",
      sliceStart: 0,
      truncatedHead: false,
      truncatedTail: text.length > context,
    };
  }
  const [rawStart, rawEnd] = range;
  const start = Math.max(0, Math.min(rawStart, text.length));
  const end = Math.max(start, Math.min(rawEnd, text.length));
  const sliceStart = Math.max(0, start - context);
  const sliceEnd = Math.min(text.length, end + context);
  const full = text.slice(start, end);
  let highlight = full;
  let highlightTail = "";
  let highlightOmitted = 0;
  if (full.length > maxHighlight) {
    const half = Math.floor(maxHighlight / 2);
    highlight = full.slice(0, half);
    highlightTail = full.slice(full.length - half);
    highlightOmitted = full.length - 2 * half;
  }
  return {
    before: text.slice(sliceStart, start),
    highlight,
    highlightTail,
    highlightOmitted,
    after: text.slice(end, sliceEnd),
    sliceStart,
    truncatedHead: sliceStart > 0,
    truncatedTail: sliceEnd < text.length,
  };
}
