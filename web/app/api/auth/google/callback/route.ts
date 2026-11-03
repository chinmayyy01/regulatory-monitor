import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import { API_URL, SESSION_COOKIE } from "@/lib/api";

const STATE_COOKIE = "regintel_oauth_state";

function fail(base: string, reason: string) {
  return NextResponse.redirect(`${base}/login?error=${encodeURIComponent(reason)}`);
}

export async function GET(request: Request) {
  const url = new URL(request.url);
  const base = process.env.APP_BASE_URL ?? url.origin;
  const clientId = process.env.GOOGLE_CLIENT_ID;
  const clientSecret = process.env.GOOGLE_CLIENT_SECRET;
  const sharedSecret = process.env.OAUTH_SHARED_SECRET;

  if (!clientId || !clientSecret || !sharedSecret) {
    return fail(base, "google is not configured");
  }

  const code = url.searchParams.get("code");
  const state = url.searchParams.get("state");
  const store = await cookies();
  const expectedState = store.get(STATE_COOKIE)?.value;
  store.delete(STATE_COOKIE);

  if (!code || !state || !expectedState || state !== expectedState) {
    return fail(base, "sign in could not be verified, try again");
  }

  const tokenResponse = await fetch("https://oauth2.googleapis.com/token", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      code,
      client_id: clientId,
      client_secret: clientSecret,
      redirect_uri: `${base}/api/auth/google/callback`,
      grant_type: "authorization_code",
    }),
  });

  const tokens = (await tokenResponse.json()) as { access_token?: string };
  if (!tokenResponse.ok || !tokens.access_token) {
    return fail(base, "google rejected the sign in");
  }

  const infoResponse = await fetch("https://openidconnect.googleapis.com/v1/userinfo", {
    headers: { Authorization: `Bearer ${tokens.access_token}` },
  });
  const info = (await infoResponse.json()) as {
    email?: string;
    email_verified?: boolean;
    name?: string;
  };

  if (!info.email || info.email_verified !== true) {
    return fail(base, "that google account has no verified email");
  }

  const exchange = await fetch(`${API_URL}/api/auth/oauth/exchange`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-OAuth-Secret": sharedSecret },
    body: JSON.stringify({ email: info.email, name: info.name ?? "" }),
    cache: "no-store",
  });

  if (!exchange.ok) {
    return fail(base, "could not create a session");
  }

  const data = (await exchange.json()) as { token: string };
  const result = NextResponse.redirect(`${base}/app`);
  result.cookies.set(SESSION_COOKIE, data.token, {
    httpOnly: true,
    sameSite: "lax",
    secure: base.startsWith("https://"),
    path: "/",
    maxAge: 60 * 60 * 24 * 7,
  });
  return result;
}
