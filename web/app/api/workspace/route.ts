import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import { isSameOrigin } from "@/lib/origin";
import { API_URL, AUTH_DISABLED, SESSION_COOKIE } from "@/lib/api";

export async function POST(request: Request) {
  if (!isSameOrigin(request)) {
    return NextResponse.json({ error: "cross-origin request rejected" }, { status: 403 });
  }
  const store = await cookies();
  const token = store.get(SESSION_COOKIE)?.value;
  if (!AUTH_DISABLED && !token) return NextResponse.json({ error: "not signed in" }, { status: 401 });

  const body = (await request.json().catch(() => ({}))) as Record<string, unknown>;
  const name = typeof body.name === "string" ? body.name.trim() : "";
  const entityType = typeof body.entityType === "string" ? body.entityType : "";
  if (name.length < 2 || entityType.length < 2) {
    return NextResponse.json({ error: "name and entity type are required" }, { status: 400 });
  }

  const response = await fetch(`${API_URL}/api/tenants`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(AUTH_DISABLED ? {} : { Authorization: `Bearer ${token}` }),
    },
    body: JSON.stringify({ name, entity_type: entityType, products: ["lending"] }),
    cache: "no-store",
  });
  const responseBody = await response.text();
  try {
    return NextResponse.json(JSON.parse(responseBody), { status: response.status });
  } catch {
    return NextResponse.json(
      { error: `Workspace request failed (${response.status}). Please try again.` },
      { status: response.status },
    );
  }
}
