import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import { API_URL, SESSION_COOKIE } from "@/lib/api";

export async function POST() {
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
