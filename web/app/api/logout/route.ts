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

  if (token) {
    await fetch(`${API_URL}/api/auth/logout`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
    });
  }

  const response = NextResponse.json({ status: "signed out" });
  response.cookies.set(SESSION_COOKIE, "", { path: "/", maxAge: 0 });
  return response;
}
