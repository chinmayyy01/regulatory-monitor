import { NextResponse } from "next/server";
import { isSameOrigin } from "@/lib/origin";
import { API_URL, SESSION_COOKIE } from "@/lib/api";

export async function POST(request: Request) {
  if (!isSameOrigin(request)) {
    return NextResponse.json({ error: "cross-origin request rejected" }, { status: 403 });
  }

  const body = (await request.json().catch(() => ({}))) as Record<string, unknown>;
  const email = typeof body.email === "string" ? body.email.trim() : "";
  const password = typeof body.password === "string" ? body.password : "";
  const workspace = typeof body.workspace === "string" ? body.workspace.trim() : "";
  const entityType = typeof body.entityType === "string" ? body.entityType : "nbfc";

  if (!email || password.length < 12 || workspace.length < 2) {
    return NextResponse.json(
      { error: "email, a 12 character password and a workspace name are required" },
      { status: 400 },
    );
  }

  const response = await fetch(`${API_URL}/api/auth/signup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, workspace, entity_type: entityType }),
    cache: "no-store",
  });

  const data = await response.json();
  if (!response.ok) {
    return NextResponse.json(data, { status: response.status });
  }

  const forwarded = request.headers.get("x-forwarded-proto");
  const protocol = forwarded ?? new URL(request.url).protocol.replace(":", "");

  const result = NextResponse.json({ user: data.user }, { status: 201 });
  result.cookies.set(SESSION_COOKIE, data.token, {
    httpOnly: true,
    sameSite: "lax",
    secure: protocol === "https",
    path: "/",
    maxAge: 60 * 60 * 24 * 7,
  });
  return result;
}
