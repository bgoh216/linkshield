const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export interface LinkResponse {
  id: number;
  short_code: string;
  long_url: string;
  created_at: string;
  is_flagged: boolean;
  is_verified_safe: boolean;
  click_count: number;
}

export async function createLink(longUrl: string, customCode?: string): Promise<LinkResponse> {
  const res = await fetch(`${API_BASE}/api/links`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ long_url: longUrl, custom_code: customCode || null }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(err.detail ?? "Failed to create link");
  }

  return res.json();
}

export async function listLinks(): Promise<LinkResponse[]> {
  const res = await fetch(`${API_BASE}/api/links`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch links");
  return res.json();
}

export function shortUrlFor(shortCode: string): string {
  // Points at our own /go/[code] page (interstitial for real browsers,
  // instant server-side redirect for bots) — not the raw backend /r/{code}.
  const appBase = process.env.NEXT_PUBLIC_APP_BASE ?? "http://localhost:3000";
  return `${appBase}/go/${shortCode}`;
}
