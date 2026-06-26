import { renderToString } from "react-dom/server";
import { beforeAll, expect, it } from "vitest";

beforeAll(() => {
  const store: Record<string, string> = {};
  (globalThis as unknown as { localStorage: Storage }).localStorage = {
    getItem: (k: string) => store[k] ?? null,
    setItem: (k: string, v: string) => {
      store[k] = v;
    },
    removeItem: (k: string) => {
      delete store[k];
    },
    clear: () => {},
    key: () => null,
    length: 0,
  } as Storage;
});

it("renders the app shell at runtime with zh-Hant default and resolved keys", async () => {
  await import("./i18n");
  const { default: App } = await import("./App");
  const html = renderToString(<App />);

  expect(html).toContain("SEC 10-K Item Extractor");
  // zh-Hant default copy renders (not raw keys)
  expect(html).toContain("運作方式");
  expect(html).toContain("Glossary");
  // no unresolved i18n keys leaked into the DOM
  expect(html).not.toMatch(/howItWorks\.toggle|summary\.title|g\.\w+\.[td]/);
});
