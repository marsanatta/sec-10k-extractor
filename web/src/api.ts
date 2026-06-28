import type { DemoEntry, ExtractRequest, ExtractionResult, ModelInfo } from "./types";

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

export async function fetchModels(): Promise<{ models: ModelInfo[]; default: string }> {
  return asJson<{ models: ModelInfo[]; default: string }>(await fetch("/api/models"));
}

export async function extractDemo(id: string): Promise<ExtractionResult> {
  return asJson<ExtractionResult>(await fetch(`/api/demo-result/${encodeURIComponent(id)}`));
}

function authHeaders(token?: string): Record<string, string> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) headers.Authorization = `Bearer ${token}`;
  return headers;
}

export async function extract(req: ExtractRequest, token?: string): Promise<ExtractionResult> {
  const resp = await fetch("/api/extract", {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify(req),
  });
  return asJson<ExtractionResult>(resp);
}

export async function extractText(
  text: string,
  token?: string,
  model?: string,
  escalate?: boolean,
): Promise<ExtractionResult> {
  const resp = await fetch("/api/extract-text", {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify({ text, model, escalate }),
  });
  return asJson<ExtractionResult>(resp);
}
