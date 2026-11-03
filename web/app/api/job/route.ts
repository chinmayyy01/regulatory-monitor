import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import { API_URL, SESSION_COOKIE } from "@/lib/api";

export async function GET(request: Request) {
  const authDisabled = process.env.AUTH_DISABLED === "true";
  const store = await cookies();
  const token = store.get(SESSION_COOKIE)?.value;
  if (!authDisabled && !token) {
    return NextResponse.json({ error: "not signed in" }, { status: 401 });
  }

  const url = new URL(request.url);
  const tenantId = Number(url.searchParams.get("tenantId"));
  const jobId = Number(url.searchParams.get("jobId"));
  if (!Number.isInteger(tenantId) || !Number.isInteger(jobId)) {
    return NextResponse.json({ error: "tenantId and jobId are required" }, { status: 400 });
  }

  const response = await fetch(`${API_URL}/api/tenants/${tenantId}/jobs/${jobId}`, {
    headers: authDisabled ? {} : { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  return NextResponse.json(await response.json(), { status: response.status });
}
