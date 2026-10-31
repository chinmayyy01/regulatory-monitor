import { cookies } from "next/headers";
import { redirect } from "next/navigation";

export const API_URL = process.env.API_URL ?? "http://localhost:8000";
export const SESSION_COOKIE = "regintel_session";

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

export async function sessionToken(): Promise<string | null> {
  const store = await cookies();
  return store.get(SESSION_COOKIE)?.value ?? null;
}

async function get<T>(path: string, token: string): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    cache: "no-store",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (response.status === 401) {
    redirect("/login");
  }
  if (!response.ok) {
    throw new Error(`API ${response.status} on ${path}`);
  }
  return response.json() as Promise<T>;
}

export async function requireToken(): Promise<string> {
  const token = await sessionToken();
  if (!token) redirect("/login");
  return token;
}

export async function listTenants(token: string): Promise<Tenant[]> {
  return get<Tenant[]>("/api/tenants", token);
}

export async function getGaps(tenantId: number, token: string): Promise<GapsResponse> {
  return get<GapsResponse>(`/api/tenants/${tenantId}/gaps`, token);
}
