import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import { API_URL, SESSION_COOKIE } from "@/lib/api";

export async function GET(request: Request) {
  const authDisabled = process.env.AUTH_DISABLED === "true";
  const store = await cookies();
  const token = store.get(SESSION_COOKIE)?.value;
  if (!authDisabled && !token) {
    return new NextResponse("not signed in", { status: 401 });
  }

  const url = new URL(request.url);
  const tenantId = Number(url.searchParams.get("tenantId"));
  const documentId = Number(url.searchParams.get("documentId"));
  if (!Number.isInteger(tenantId) || !Number.isInteger(documentId)) {
    return new NextResponse("bad request", { status: 400 });
  }

  const response = await fetch(
    `${API_URL}/api/tenants/${tenantId}/documents/${documentId}/pdf`,
    { headers: authDisabled ? {} : { Authorization: `Bearer ${token}` }, cache: "no-store" },
  );
  if (!response.ok) {
    return new NextResponse("not found", { status: response.status });
  }

  return new NextResponse(response.body, {
    headers: {
      "Content-Type": "application/pdf",
      "Content-Disposition": "inline",
    },
  });
}
