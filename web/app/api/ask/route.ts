import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import { API_URL, SESSION_COOKIE } from "@/lib/api";

export async function POST(request: Request) {
  const store = await cookies();
  const token = store.get(SESSION_COOKIE)?.value;
  if (!token) {
    return NextResponse.json({ error: "not signed in" }, { status: 401 });
  }

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "invalid json" }, { status: 400 });
  }

  const { tenantId, question } = (body ?? {}) as {
    tenantId?: unknown;
    question?: unknown;
  };

  if (!Number.isInteger(tenantId) || typeof question !== "string" || question.length < 3) {
    return NextResponse.json({ error: "tenantId and question are required" }, { status: 400 });
  }

  const response = await fetch(
    `${API_URL}/api/tenants/${tenantId as number}/ask`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ question: question.slice(0, 500) }),
      cache: "no-store",
    },
  );

  const data = await response.json();
  return NextResponse.json(data, { status: response.status });
}
