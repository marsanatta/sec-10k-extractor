import { describe, expect, it } from "vitest";
import type { Item } from "../types";
import {
  bandLabel,
  groupByPart,
  itemColor,
  sliceAroundRange,
  statusLabel,
} from "./format";

function makeItem(overrides: Partial<Item> = {}): Item {
  return {
    item_id: "I.1",
    part: "I",
    item: "1",
    title: "Business",
    text: "",
    char_range: [0, 10],
    status: "present",
    confidence: { band: "high", score: 0.9, signals: [] },
    provenance: { extractors: [], checks_passed: [], checks_failed: [] },
    ...overrides,
  };
}

describe("itemColor", () => {
  it("present + high -> green", () => {
    expect(itemColor(makeItem())).toBe("green");
  });

  it("present + medium -> amber", () => {
    expect(itemColor(makeItem({ confidence: { band: "medium", score: 0.6, signals: [] } }))).toBe(
      "amber",
    );
  });

  it("present + low -> red", () => {
    expect(itemColor(makeItem({ confidence: { band: "low", score: 0.3, signals: [] } }))).toBe(
      "red",
    );
  });

  it("present + boundary disagreement -> red even at high band", () => {
    const flagged = makeItem({
      provenance: { extractors: [], checks_passed: [], checks_failed: ["boundary_xcheck"] },
    });
    expect(itemColor(flagged)).toBe("red");
  });

  it("legitimately_absent -> muted", () => {
    expect(itemColor(makeItem({ status: "legitimately_absent" }))).toBe("muted");
  });

  it("extraction_failure -> red", () => {
    expect(itemColor(makeItem({ status: "extraction_failure" }))).toBe("red");
  });
});

describe("bandLabel / statusLabel", () => {
  it("maps bands", () => {
    expect(bandLabel("high")).toMatch(/High/);
    expect(bandLabel("unscored")).toMatch(/Unscored/);
  });
  it("maps statuses", () => {
    expect(statusLabel("extraction_failure")).toMatch(/failure/i);
    expect(statusLabel("legitimately_absent")).toMatch(/absent/i);
  });
});

describe("groupByPart", () => {
  it("groups and orders Parts I->IV regardless of input order", () => {
    const items = [
      makeItem({ part: "III", item: "10" }),
      makeItem({ part: "I", item: "1" }),
      makeItem({ part: "II", item: "7" }),
      makeItem({ part: "I", item: "1A" }),
    ];
    const groups = groupByPart(items);
    expect(groups.map((g) => g.part)).toEqual(["I", "II", "III"]);
    expect(groups[0].items).toHaveLength(2);
  });
});

describe("sliceAroundRange", () => {
  const text = "0123456789ABCDEFGHIJ";

  it("splits before/highlight/after for a mid range", () => {
    const s = sliceAroundRange(text, [5, 10], 2);
    expect(s.before).toBe("34");
    expect(s.highlight).toBe("56789");
    expect(s.after).toBe("AB");
    expect(s.sliceStart).toBe(3);
    expect(s.truncatedHead).toBe(true);
    expect(s.truncatedTail).toBe(true);
  });

  it("range at start has no head truncation and empty before", () => {
    const s = sliceAroundRange(text, [0, 4], 2);
    expect(s.before).toBe("");
    expect(s.highlight).toBe("0123");
    expect(s.after).toBe("45");
    expect(s.truncatedHead).toBe(false);
  });

  it("range at end has no tail truncation and empty after", () => {
    const s = sliceAroundRange(text, [18, 20], 2);
    expect(s.highlight).toBe("IJ");
    expect(s.after).toBe("");
    expect(s.truncatedTail).toBe(false);
  });

  it("null range returns head-capped before only", () => {
    const s = sliceAroundRange(text, null, 5);
    expect(s.before).toBe("01234");
    expect(s.highlight).toBe("");
    expect(s.truncatedTail).toBe(true);
  });

  it("clamps an out-of-bounds range to text length", () => {
    const s = sliceAroundRange(text, [15, 999], 100);
    expect(s.highlight).toBe("FGHIJ");
    expect(s.after).toBe("");
    expect(s.truncatedTail).toBe(false);
  });
});
