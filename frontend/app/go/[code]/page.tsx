import { headers } from "next/headers";
import { redirect } from "next/navigation";
import { isBot } from "@/lib/botDetection";
import InterstitialRedirect from "./InterstitialRedirect";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export default async function GoPage({ params }: { params: { code: string } }) {
  const userAgent = (await headers()).get("user-agent");

  if (isBot(userAgent)) {
    // Bots/crawlers/CLI tools never run JS — send them straight through the
    // plain backend redirect, same path used before this feature existed.
    redirect(`${API_BASE}/r/${params.code}`);
  }

  // Real browsers land here: render a client component that collects
  // enrichment data, posts it, then redirects itself.
  return <InterstitialRedirect code={params.code} />;
}
