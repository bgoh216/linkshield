"use client";

import { useEffect, useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export default function InterstitialRedirect({ code }: { code: string }) {
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function go() {
      const metadata = {
        screen_width: window.screen.width,
        screen_height: window.screen.height,
        viewport_width: window.innerWidth,
        viewport_height: window.innerHeight,
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        language: navigator.language,
      };

      try {
        const res = await fetch(`${API_BASE}/api/links/${code}/click`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(metadata),
        });

        if (!res.ok) {
          const err = await res.json().catch(() => ({ detail: "Link unavailable" }));
          setError(err.detail ?? "This link could not be opened");
          return;
        }

        const data = await res.json();
        window.location.replace(data.redirect_url);
      } catch {
        setError("Could not reach the server. Check your connection.");
      }
    }

    go();
  }, [code]);

  return (
    <main className="flex min-h-screen items-center justify-center px-4">
      <div className="text-center space-y-2">
        {error ? (
          <p className="text-red-600 text-sm">{error}</p>
        ) : (
          <>
            <div className="animate-pulse text-sm text-slate-500">
              Redirecting you safely...
            </div>
            <p className="text-xs text-slate-400">Verifying link before continuing</p>
          </>
        )}
      </div>
    </main>
  );
}
