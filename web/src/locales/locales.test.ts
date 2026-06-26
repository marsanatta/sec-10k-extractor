import { describe, expect, it } from "vitest";
import en from "./en.json";
import zhHant from "./zh-Hant.json";

function flattenKeys(obj: unknown, prefix = ""): string[] {
  if (obj === null || typeof obj !== "object") return [prefix];
  return Object.entries(obj as Record<string, unknown>).flatMap(([k, v]) =>
    flattenKeys(v, prefix ? `${prefix}.${k}` : k),
  );
}

describe("locale key parity", () => {
  it("en and zh-Hant expose the identical set of keys", () => {
    const enKeys = flattenKeys(en).sort();
    const zhKeys = flattenKeys(zhHant).sort();
    const missingInZh = enKeys.filter((k) => !zhKeys.includes(k));
    const extraInZh = zhKeys.filter((k) => !enKeys.includes(k));
    expect({ missingInZh, extraInZh }).toEqual({ missingInZh: [], extraInZh: [] });
  });

  it("has no empty string values", () => {
    const emptyEn = flattenKeys(en).filter((k) => resolve(en, k) === "");
    const emptyZh = flattenKeys(zhHant).filter((k) => resolve(zhHant, k) === "");
    expect({ emptyEn, emptyZh }).toEqual({ emptyEn: [], emptyZh: [] });
  });
});

function resolve(obj: unknown, dotted: string): unknown {
  return dotted.split(".").reduce<unknown>((acc, part) => {
    if (acc && typeof acc === "object") return (acc as Record<string, unknown>)[part];
    return undefined;
  }, obj);
}
