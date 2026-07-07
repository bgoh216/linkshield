"use client";

import { useEffect, useState } from "react";
import {
  SgdsAlert,
  SgdsBadge,
  SgdsButton,
  SgdsDescriptionList,
  SgdsDescriptionListGroup,
  SgdsDivider,
  SgdsIcon,
  SgdsIconButton,
  SgdsInput,
  SgdsLink,
} from "@govtechsg/sgds-web-component/react";
import { createLink, listLinks, shortUrlFor, LinkResponse } from "@/lib/api";

function renderStatusBadge(link: LinkResponse) {
  if (link.is_flagged) {
    return (
      <SgdsBadge variant="danger">
        <SgdsIcon slot="icon" name="exclamation-triangle-fill" size="xs" />
        Flagged unsafe
      </SgdsBadge>
    );
  }
  if (link.is_verified_safe) {
    return (
      <SgdsBadge variant="success" outlined>
        <SgdsIcon slot="icon" name="shield-tick" size="xs" />
        Verified safe
      </SgdsBadge>
    );
  }
  return (
    <SgdsBadge variant="neutral" outlined>
      Unverified
    </SgdsBadge>
  );
}

export default function HomePage() {
  const [longUrl, setLongUrl] = useState("");
  const [customCode, setCustomCode] = useState("");
  const [links, setLinks] = useState<LinkResponse[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [copiedId, setCopiedId] = useState<number | null>(null);
  const [newLink, setNewLink] = useState<LinkResponse | null>(null);
  const [showCustomCode, setShowCustomCode] = useState(false);

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
      const created = await createLink(longUrl, customCode || undefined);
      setLongUrl("");
      setCustomCode("");
      await refresh();
      setNewLink(created);
    } catch (err: any) {
      setError(err.message ?? "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  async function handleCopy(id: number, url: string) {
    await navigator.clipboard.writeText(url);
    setCopiedId(id);
    setTimeout(() => setCopiedId((current) => (current === id ? null : current)), 1500);
  }

  return (
    <main className="min-h-screen" style={{ background: "var(--sgds-bg-alternate)" }}>
      <div
        className="mx-auto px-6 py-12 sm:px-10 lg:py-16"
        style={{ maxWidth: "var(--sgds-container-max-width-lg)" }}
      >
        {/* Header */}
        <div className="flex flex-wrap items-start justify-between gap-6">
          <div className="flex items-start gap-4">
            <SgdsIcon name="shield-tick" size="xl" style={{ color: "var(--sgds-primary-color-default)" }} />
            <div>
              <h1
                className="m-0"
                style={{
                  fontFamily: "var(--sgds-font-family-brand)",
                  fontSize: "var(--sgds-font-size-display-sm)",
                  fontWeight: "var(--sgds-font-weight-bold)",
                  color: "var(--sgds-color-default)",
                  lineHeight: 1.15,
                }}
              >
                LinkShield
              </h1>
              <p
                className="m-0 mt-2"
                style={{ fontSize: "var(--sgds-font-size-subtitle-md)", color: "var(--sgds-color-subtle)" }}
              >
                A short link you can trust.
              </p>
            </div>
          </div>
          <SgdsBadge variant="success" outlined>
            <SgdsIcon slot="icon" name="shield-tick" size="xs" />
            Checked against threat intel
          </SgdsBadge>
        </div>

        <div className="my-10">
          <SgdsDivider />
        </div>

        {/* Form + trust panel */}
        <div className="grid grid-cols-1 gap-8 lg:grid-cols-12 lg:gap-10">
          <div
            className="lg:col-span-7"
            style={{
              background: "var(--sgds-surface-default)",
              border: "1px solid var(--sgds-border-color-default)",
              borderRadius: "var(--sgds-border-radius-lg)",
              padding: "var(--sgds-padding-2-xl)",
            }}
          >
            <p
              className="m-0 mb-1 uppercase"
              style={{
                fontSize: "var(--sgds-font-size-label-sm)",
                fontWeight: "var(--sgds-font-weight-semibold)",
                color: "var(--sgds-color-subtle)",
                letterSpacing: "0.06em",
              }}
            >
              Shorten a link
            </p>
            <h2
              className="m-0 mb-6"
              style={{
                fontSize: "var(--sgds-font-size-heading-sm)",
                fontWeight: "var(--sgds-font-weight-semibold)",
                color: "var(--sgds-color-default)",
              }}
            >
              Paste a URL to get started
            </h2>

            <form onSubmit={handleSubmit} className="flex flex-col gap-5">
              <SgdsInput
                type="url"
                required
                label="Long URL"
                placeholder="https://example.com/very/long/link"
                value={longUrl}
                onSgdsInput={(e) => setLongUrl((e.target as any).value)}
              >
                <SgdsIcon slot="icon" name="link" />
              </SgdsInput>
              <div>
                <SgdsButton
                  type="button"
                  variant="ghost"
                  size="sm"
                  hasLeftIconSlot
                  onClick={() => setShowCustomCode((v) => !v)}
                  style={{ paddingLeft: 0 }}
                >
                  <SgdsIcon slot="leftIcon" name={showCustomCode ? "chevron-up" : "chevron-down"} size="xs" />
                  Customize your short link
                </SgdsButton>

                {showCustomCode && (
                  <div className="mt-3">
                    <SgdsInput
                      type="text"
                      label="Custom code"
                      prefix="/go/"
                      hintText="Optional — we'll generate one if left blank"
                      placeholder="my-custom-code"
                      value={customCode}
                      onSgdsInput={(e) => setCustomCode((e.target as any).value)}
                    />
                  </div>
                )}
              </div>
              <div className="mt-1">
                <SgdsButton type="submit" loading={loading} disabled={loading} hasRightIconSlot>
                  {loading ? "Shortening..." : "Shorten link"}
                  <SgdsIcon slot="rightIcon" name="arrow-right" />
                </SgdsButton>
              </div>
              {error && <SgdsAlert variant="danger">{error}</SgdsAlert>}
            </form>

            {newLink && (
              <div className="mt-5">
                <SgdsAlert variant="success" show dismissible onSgdsHide={() => setNewLink(null)}>
                  <span style={{ fontWeight: "var(--sgds-font-weight-semibold)" }}>
                    Your short link is ready
                  </span>
                  <div
                    className="mt-2 flex w-full items-center gap-3"
                    style={{
                      border: "1px solid var(--sgds-border-color-default)",
                      borderRadius: "var(--sgds-border-radius-md)",
                      padding: "var(--sgds-padding-sm) var(--sgds-padding-md)",
                      background: "var(--sgds-surface-default)",
                      overflow: "hidden",
                      minWidth: 0,
                    }}
                  >
                    <SgdsLink size="md" style={{ minWidth: 0, overflow: "hidden", flex: "1 1 auto" }}>
                      <a
                        href={shortUrlFor(newLink.short_code)}
                        target="_blank"
                        rel="noreferrer"
                        style={{
                          fontWeight: "var(--sgds-font-weight-semibold)",
                          display: "block",
                          width: "100%",
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                          whiteSpace: "nowrap",
                        }}
                      >
                        {shortUrlFor(newLink.short_code).replace(/^https?:\/\//, "")}
                      </a>
                    </SgdsLink>
                    <SgdsIconButton
                      size="sm"
                      style={{ flexShrink: 0 }}
                      name={copiedId === newLink.id ? "check" : "copy"}
                      ariaLabel="Copy short link"
                      onClick={() => handleCopy(newLink.id, shortUrlFor(newLink.short_code))}
                    />
                  </div>
                </SgdsAlert>
              </div>
            )}
          </div>

          <div className="lg:col-span-5">
            <SgdsDescriptionListGroup stacked hasTitleSlot>
              <span
                slot="title"
                style={{
                  fontSize: "var(--sgds-font-size-heading-sm)",
                  fontWeight: "var(--sgds-font-weight-semibold)",
                  color: "var(--sgds-color-default)",
                }}
              >
                How it works
              </span>

              <SgdsDescriptionList stacked>
                <SgdsIcon
                  name="shield-tick"
                  size="sm"
                  style={{ marginRight: "0.5rem", color: "var(--sgds-success-color-default)", verticalAlign: "-2px" }}
                />
                Checked automatically
                <span slot="data">
                  Every link is screened against known malware and phishing sources before it goes live.
                </span>
              </SgdsDescriptionList>

              <SgdsDescriptionList stacked>
                <SgdsIcon
                  name="clock"
                  size="sm"
                  style={{ marginRight: "0.5rem", color: "var(--sgds-primary-color-default)", verticalAlign: "-2px" }}
                />
                Redirects instantly
                <span slot="data">
                  Visitors land on the destination in milliseconds — no interstitial for trusted links.
                </span>
              </SgdsDescriptionList>

              <SgdsDescriptionList stacked>
                <SgdsIcon
                  name="trend-up"
                  size="sm"
                  style={{ marginRight: "0.5rem", color: "var(--sgds-accent-color-default)", verticalAlign: "-2px" }}
                />
                Tracked for you
                <span slot="data">Click counts update live, so you always know how a link is performing.</span>
              </SgdsDescriptionList>
            </SgdsDescriptionListGroup>
          </div>
        </div>

        <div className="my-10">
          <SgdsDivider />
        </div>

        {/* Links table */}
        <div className="mb-5 flex items-center justify-between gap-4">
          <h2
            className="m-0"
            style={{
              fontSize: "var(--sgds-font-size-heading-sm)",
              fontWeight: "var(--sgds-font-weight-semibold)",
              color: "var(--sgds-color-default)",
            }}
          >
            Your links
          </h2>
          {links.length > 0 && (
            <SgdsBadge variant="neutral" outlined>
              {links.length} {links.length === 1 ? "link" : "links"}
            </SgdsBadge>
          )}
        </div>

        {links.length === 0 ? (
          <div
            className="flex flex-col items-center gap-3 text-center"
            style={{
              padding: "var(--sgds-padding-3-xl) var(--sgds-padding-2-xl)",
              border: "1px dashed var(--sgds-border-color-default)",
              borderRadius: "var(--sgds-border-radius-lg)",
              color: "var(--sgds-color-subtle)",
            }}
          >
            <SgdsIcon name="link" size="lg" style={{ color: "var(--sgds-color-muted)" }} />
            <p className="m-0" style={{ fontSize: "var(--sgds-font-size-body-md)" }}>
              No links yet — shorten your first URL above and it'll show up here.
            </p>
          </div>
        ) : (
            <div
              className="flex flex-col"
              style={{
                border: "1px solid var(--sgds-border-color-default)",
                borderRadius: "var(--sgds-border-radius-lg)",
                background: "var(--sgds-surface-default)",
                maxHeight: "28rem",
                overflowY: "auto",
              }}
            >
              {links.map((link, index) => {
                const url = shortUrlFor(link.short_code);
                return (
                  <div
                    key={link.id}
                    className="flex flex-col gap-2"
                    style={{
                      padding: "var(--sgds-padding-lg)",
                      borderTop:
                        index === 0 ? "none" : "1px solid var(--sgds-border-color-default)",
                    }}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <SgdsLink size="sm">
                        <a
                          href={url}
                          target="_blank"
                          rel="noreferrer"
                          style={{
                            display: "inline-block",
                            maxWidth: "100%",
                            overflow: "hidden",
                            textOverflow: "ellipsis",
                            whiteSpace: "nowrap",
                          }}
                        >
                          {url.replace(/^https?:\/\//, "")}
                        </a>
                      </SgdsLink>
                      <SgdsIconButton
                        size="sm"
                        style={{ flexShrink: 0 }}
                        name={copiedId === link.id ? "check" : "copy"}
                        ariaLabel="Copy short link"
                        onClick={() => handleCopy(link.id, url)}
                      />
                    </div>
                    <span
                      title={link.long_url}
                      style={{
                        display: "block",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap",
                        fontSize: "var(--sgds-font-size-body-sm)",
                        color: "var(--sgds-color-subtle)",
                      }}
                    >
                      {link.long_url}
                    </span>
                    <div className="flex items-center justify-between gap-2">
                      <span
                        style={{
                          fontSize: "var(--sgds-font-size-body-sm)",
                          color: "var(--sgds-color-subtle)",
                          fontVariantNumeric: "tabular-nums",
                        }}
                      >
                        {link.click_count.toLocaleString()} clicks
                      </span>
                      {renderStatusBadge(link)}
                    </div>
                  </div>
                );
              })}
            </div>
        )}
      </div>
    </main>
  );
}
