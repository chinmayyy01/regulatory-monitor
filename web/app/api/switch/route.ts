import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import { isSameOrigin } from "@/lib/origin";
import { API_URL, SESSION_COOKIE } from "@/lib/api";

export async function POST(request: Request) {
  if (!isSameOrigin(request)) {
    return NextResponse.json({ error: "cross-origin request rejected" }, { status: 403 });
  }
  const store = await cookies();
  const token = store.get(SESSION_COOKIE)?.value;
  if (!token) return NextResponse.json({ error: "not signed in" }, { status: 401 });

  const body = (await request.json().catch(() => ({}))) as { tenantId?: unknown };
  const tenantId = Number(body.tenantId);
  if (!Number.isInteger(tenantId)) {
    return NextResponse.json({ error: "tenantId is required" }, { status: 400 });
  }

  const response = await fetch(`${API_URL}/api/auth/switch/${tenantId}`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  return NextResponse.json(await response.json(), { status: response.status });
}
