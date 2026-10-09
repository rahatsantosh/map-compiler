export interface ConsoleResult {
  console: string | null;
  graph: unknown | null;
  error: boolean;
}

export interface Dataset {
  name: string;
  path: string;
  size_mb: number;
}

export async function runScript(script: string, clickHash: string): Promise<ConsoleResult> {
  const params = new URLSearchParams({ click_hash: clickHash, request_script: script });
  const res = await fetch(`/std/?${params}`);
  return res.json();
}

export function buildWmsUrl(script: string, clickHash: string): string {
  const params = new URLSearchParams({ click_hash: clickHash, request_script: script });
  return `/wms/?${params}&`;
}

export async function fetchDatasets(): Promise<Dataset[]> {
  const res = await fetch("/api/datasets/");
  const data = await res.json();
  return data.datasets;
}
