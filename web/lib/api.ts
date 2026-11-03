import { cookies } from "next/headers";
import { redirect } from "next/navigation";

export const API_URL = process.env.API_URL ?? "http://localhost:8000";
export const SESSION_COOKIE = "regintel_session";
export const AUTH_DISABLED = process.env.AUTH_DISABLED === "true";

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
  policy_span: { start: number; end: number } | null;
  page: number | null;
  document_id: number | null;
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
  unsupported: number;
  claims: Claim[];
};

export async function sessionToken(): Promise<string | null> {
  const store = await cookies();
  return store.get(SESSION_COOKIE)?.value ?? null;
}

async function get<T>(path: string, token: string): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    cache: "no-store",
    headers: AUTH_DISABLED ? {} : { Authorization: `Bearer ${token}` },
  });
  if (response.status === 401) {
    redirect("/login");
  }
  if (!response.ok) {
    throw new Error(`API ${response.status} on ${path}`);
  }
  return response.json() as Promise<T>;
}

export type SessionUser = {
  id: number;
  email: string;
  tenant_id: number;
  role: string;
};

export async function currentUser(token: string): Promise<SessionUser | null> {
  try {
    const response = await fetch(`${API_URL}/api/auth/me`, {
      cache: "no-store",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!response.ok) {
      return null;
    }
    return (await response.json()) as SessionUser;
  } catch {
    return null;
  }
}

export async function requireToken(): Promise<string> {
  if (AUTH_DISABLED) return "";
  const token = await sessionToken();
  if (!token) redirect("/login");
  return token;
}

export async function listTenants(token: string): Promise<Tenant[]> {
  return get<Tenant[]>("/api/tenants", token);
}

export type Membership = { tenant_id: number; name: string; role: string };

export async function listMemberships(token: string): Promise<Membership[]> {
  return get<Membership[]>("/api/auth/tenants", token);
}

export async function getGaps(tenantId: number, token: string): Promise<GapsResponse> {
  return get<GapsResponse>(`/api/tenants/${tenantId}/gaps`, token);
}

export type Change = {
  obligation_id: number;
  before: string | null;
  after: string | null;
  direction: "new" | "worsened" | "improved" | "dropped";
  action: string;
};

export type ChangesResponse = {
  from_run: string | null;
  to_run: string | null;
  changes: Change[];
};

export type ObligationDetail = {
  obligation_id: number;
  action: string;
  condition: string;
  modality: string;
  scope_entities: string[];
  valid_from: string | null;
  regulation_clause_id: number;
  regulation_text: string;
  regulation_section: string | null;
  regulation_page: number | null;
  regulation_title: string;
  verdict: string | null;
  confidence: number | null;
  evidence_regulation: string;
  evidence_policy: string;
  reason: string;
  policy_clause_id: number | null;
  policy_text: string | null;
  policy_section: string | null;
  policy_page: number | null;
  policy_title: string | null;
  policy_span: { start: number; end: number } | null;
  policy_document_id: number | null;
};

export async function getObligationDetail(
  tenantId: number,
  obligationId: number,
  token: string,
): Promise<ObligationDetail> {
  return get<ObligationDetail>(`/api/tenants/${tenantId}/obligations/${obligationId}`, token);
}

export async function listChanges(tenantId: number, token: string): Promise<ChangesResponse> {
  return get<ChangesResponse>(`/api/tenants/${tenantId}/changes`, token);
}

export type DocumentRow = {
  id: number;
  title: string;
  doc_type: string;
  version: string | null;
  effective_from: string | null;
  page_count: number;
  clauses: number;
  created_at: string;
};

export async function listDocuments(tenantId: number, token: string): Promise<DocumentRow[]> {
  return get<DocumentRow[]>(`/api/tenants/${tenantId}/documents`, token);
}
