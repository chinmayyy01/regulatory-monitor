export const API_URL = process.env.API_URL ?? "http://localhost:8000";

export type Tenant = {
  id: number;
  name: string;
  entity_type: string;
  license_type: string | null;
  products: string[];
  documents: number;
  clauses: number;
};

export type Gap = {
  obligation_id: number;
  action: string;
  condition: string;
  modality: string;
  verdict: "satisfied" | "partial" | "missing" | "stale";
  confidence: number;
  evidence_regulation: string;
  evidence_policy: string;
  reason: string;
  clause_text: string | null;
  section_no: string | null;
  document_title: string | null;
};

export type GapsResponse = {
  tenant_id: number;
  run_id: string | null;
  summary: Record<string, number>;
  gaps: Gap[];
};

export type Citation = {
  kind: "regulation" | "policy";
  clause_id: number;
  label: string;
  quote: string;
  span: { start: number; end: number };
};

export type Claim = { text: string; citations: Citation[] };

export type AskResponse = {
  question: string;
  insufficient: boolean;
  rejected: number;
  claims: Claim[];
};

async function get<T>(path: string): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`API ${response.status} on ${path}`);
  }
  return response.json() as Promise<T>;
}

export const listTenants = () => get<Tenant[]>("/api/tenants");
export const getGaps = (tenantId: number) =>
  get<GapsResponse>(`/api/tenants/${tenantId}/gaps`);

export async function ask(tenantId: number, question: string): Promise<AskResponse> {
  const response = await fetch(`${API_URL}/api/tenants/${tenantId}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(`API ${response.status}`);
  }
  return response.json() as Promise<AskResponse>;
}
