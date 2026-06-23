import type { DemoEntry, ExtractRequest, ExtractionResult } from "./types";

async function asJson<T>(resp: Response): Promise<T> {
  const body = await resp.json().catch(() => null);
  if (!resp.ok) {
    const message =
      body && typeof body.error === "string"
        ? body.error
        : `Request failed (${resp.status})`;
    throw new Error(message);
  }
  return body as T;
}

export async function fetchDemos(): Promise<DemoEntry[]> {
  return asJson<DemoEntry[]>(await fetch("/api/demo"));
}

export async function fetchEval(): Promise<string> {
  const body = await asJson<{ markdown: string }>(await fetch("/api/eval"));
  return body.markdown;
}

export async function extract(req: ExtractRequest): Promise<ExtractionResult> {
  const resp = await fetch("/api/extract", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  return asJson<ExtractionResult>(resp);
}
