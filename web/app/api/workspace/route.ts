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

  const body = (await request.json().catch(() => ({}))) as Record<string, unknown>;
  const name = typeof body.name === "string" ? body.name.trim() : "";
  const entityType = typeof body.entityType === "string" ? body.entityType : "";
  if (name.length < 2 || entityType.length < 2) {
    return NextResponse.json({ error: "name and entity type are required" }, { status: 400 });
  }

  const response = await fetch(`${API_URL}/api/tenants`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify({ name, entity_type: entityType, products: ["lending"] }),
    cache: "no-store",
  });
  return NextResponse.json(await response.json(), { status: response.status });
}
