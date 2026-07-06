"use client";

import { useEffect, useState } from "react";
import { createLink, listLinks, shortUrlFor, LinkResponse } from "@/lib/api";

export default function HomePage() {
  const [longUrl, setLongUrl] = useState("");
  const [customCode, setCustomCode] = useState("");
  const [links, setLinks] = useState<LinkResponse[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function refresh() {
    try {
      const data = await listLinks();
      setLinks(data);
    } catch (e) {
      // non-fatal on initial load
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await createLink(longUrl, customCode || undefined);
      setLongUrl("");
      setCustomCode("");
      await refresh();
    } catch (err: any) {
      setError(err.message ?? "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto max-w-2xl px-4 py-12">
      <h1 className="text-2xl font-semibold mb-1">LinkShield</h1>
      <p className="text-slate-500 mb-8">A short link you can trust.</p>

      <form onSubmit={handleSubmit} className="space-y-3 mb-10">
        <input
          type="url"
          required
          placeholder="https://example.com/very/long/link"
          value={longUrl}
          onChange={(e) => setLongUrl(e.target.value)}
          className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
        />
        <input
          type="text"
          placeholder="custom code (optional)"
          value={customCode}
          onChange={(e) => setCustomCode(e.target.value)}
          className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
        />
        <button
          type="submit"
          disabled={loading}
          className="rounded-md bg-slate-900 px-4 py-2 text-sm text-white disabled:opacity-50"
        >
          {loading ? "Shortening..." : "Shorten link"}
        </button>
        {error && <p className="text-sm text-red-600">{error}</p>}
      </form>

      <h2 className="text-sm font-medium text-slate-500 mb-3">Your links</h2>
      <ul className="space-y-3">
        {links.map((link) => (
          <li
            key={link.id}
            className="rounded-md border border-slate-200 p-3 text-sm flex flex-col gap-1"
          >
            <div className="flex items-center justify-between">
              <a
                href={shortUrlFor(link.short_code)}
                target="_blank"
                rel="noreferrer"
                className="font-medium text-blue-600"
              >
                {shortUrlFor(link.short_code)}
              </a>
              {link.is_flagged && (
                <span className="text-xs text-red-600 font-medium">flagged unsafe</span>
              )}
            </div>
            <span className="text-slate-500 truncate">{link.long_url}</span>
            <span className="text-slate-400 text-xs">{link.click_count} clicks</span>
          </li>
        ))}
        {links.length === 0 && (
          <li className="text-slate-400 text-sm">No links yet.</li>
        )}
      </ul>
    </main>
  );
}
