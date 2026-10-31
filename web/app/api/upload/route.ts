import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import { isSameOrigin } from "@/lib/origin";
import { API_URL, SESSION_COOKIE } from "@/lib/api";

const MAX_BYTES = 10 * 1024 * 1024;

export async function POST(request: Request) {
  if (!isSameOrigin(request)) {
    return NextResponse.json({ error: "cross-origin request rejected" }, { status: 403 });
  }

  const store = await cookies();
  const token = store.get(SESSION_COOKIE)?.value;
  if (!token) return NextResponse.json({ error: "not signed in" }, { status: 401 });

  const form = await request.formData();
  const tenantId = Number(form.get("tenantId"));
  const file = form.get("file");

  if (!Number.isInteger(tenantId)) {
    return NextResponse.json({ error: "tenantId is required" }, { status: 400 });
  }
  if (!(file instanceof File)) {
    return NextResponse.json({ error: "file is required" }, { status: 400 });
  }
  if (!file.name.toLowerCase().endsWith(".pdf")) {
    return NextResponse.json({ error: "only .pdf files are accepted" }, { status: 400 });
  }
  if (file.size > MAX_BYTES) {
    return NextResponse.json({ error: "file is larger than 10 MB" }, { status: 413 });
  }

  const body = new FormData();
  body.append("file", file, file.name);

  const response = await fetch(`${API_URL}/api/tenants/${tenantId}/documents`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body,
    cache: "no-store",
  });

  return NextResponse.json(await response.json(), { status: response.status });
}
