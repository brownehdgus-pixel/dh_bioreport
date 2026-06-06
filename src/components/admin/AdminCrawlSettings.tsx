"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  formatCrawlConfigJson,
  parseCrawlConfigText,
  validateCrawlConfig,
} from "@/lib/crawlConfigSchema";

const textareaClass =
  "w-full min-h-[420px] rounded-md border border-memo-border bg-memo-bg px-3 py-2 font-mono text-xs text-memo-ink outline-none focus:border-memo-accent focus:ring-1 focus:ring-memo-accent/30";

export function AdminCrawlSettings() {
  const [content, setContent] = useState("");
  const [loadError, setLoadError] = useState("");
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const [message, setMessage] = useState("");
  const [saving, setSaving] = useState(false);
  const [loaded, setLoaded] = useState(false);

  const loadConfig = useCallback(async () => {
    setLoadError("");
    setMessage("");
    try {
      const res = await fetch("/api/admin/crawl-config");
      if (!res.ok) {
        const data = (await res.json()) as { error?: string };
        throw new Error(data.error || `HTTP ${res.status}`);
      }
      const data = (await res.json()) as { content: string };
      setContent(data.content);
      setLoaded(true);
    } catch (err) {
      setLoadError(err instanceof Error ? err.message : "Failed to load config");
    }
  }, []);

  useEffect(() => {
    void loadConfig();
  }, [loadConfig]);

  function runValidation(text: string) {
    const parsed = parseCrawlConfigText(text);
    if (!parsed.ok) {
      setValidationErrors([parsed.error]);
      return false;
    }
    const result = validateCrawlConfig(parsed.data);
    if (!result.ok) {
      setValidationErrors(result.errors);
      return false;
    }
    setValidationErrors([]);
    return true;
  }

  function handleChange(text: string) {
    setContent(text);
    setMessage("");
    runValidation(text);
  }

  function handleFormat() {
    const parsed = parseCrawlConfigText(content);
    if (!parsed.ok) {
      setValidationErrors([parsed.error]);
      return;
    }
    const result = validateCrawlConfig(parsed.data);
    if (!result.ok) {
      setValidationErrors(result.errors);
      return;
    }
    setContent(formatCrawlConfigJson(result.data));
    setValidationErrors([]);
  }

  async function handleCopy() {
    if (!runValidation(content)) {
      setMessage("JSON validation failed — fix errors before copying.");
      return;
    }
    try {
      await navigator.clipboard.writeText(content);
      setMessage("Copied to clipboard.");
    } catch {
      setMessage("Copy failed — select the text manually.");
    }
  }

  async function handleSave() {
    if (!runValidation(content)) {
      setMessage("Fix validation errors before saving.");
      return;
    }
    setSaving(true);
    setMessage("");
    try {
      const res = await fetch("/api/admin/crawl-config", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content }),
      });
      const data = (await res.json()) as { ok?: boolean; message?: string; error?: string; errors?: string[] };
      if (!res.ok) {
        if (data.errors?.length) {
          setValidationErrors(data.errors);
        }
        throw new Error(data.error || `HTTP ${res.status}`);
      }
      setMessage(data.message || "Saved to GitHub.");
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Save failed");
    } finally {
      setSaving(false);
    }
  }

  async function handleLogout() {
    await fetch("/api/admin/logout", { method: "POST" });
    window.location.reload();
  }

  return (
    <div className="mx-auto min-h-dvh max-w-3xl">
      <header className="border-b border-memo-border bg-memo-surface px-4 pb-5 pt-6">
        <div className="mb-3 flex items-center justify-between gap-2">
          <Link href="/admin" className="text-sm text-memo-muted hover:text-memo-ink">
            ← 뉴스 입력
          </Link>
          <button
            type="button"
            onClick={() => void handleLogout()}
            className="text-sm text-memo-muted hover:text-memo-ink"
          >
            로그아웃
          </button>
        </div>
        <h1 className="text-lg font-semibold text-memo-ink">크롤 설정</h1>
        <p className="mt-1 text-sm text-memo-muted">
          <code className="text-xs">data/crawl_config.json</code> — RSS·키워드·가중치·한도
        </p>
      </header>

      <main className="space-y-4 px-4 py-6">
        {loadError && (
          <p className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
            {loadError}
          </p>
        )}

        {!loaded && !loadError && (
          <p className="text-sm text-memo-muted">설정 불러오는 중…</p>
        )}

        <textarea
          className={textareaClass}
          value={content}
          onChange={(e) => handleChange(e.target.value)}
          spellCheck={false}
          aria-label="Crawl config JSON"
        />

        {validationErrors.length > 0 && (
          <div className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900">
            <p className="font-medium">Validation errors</p>
            <ul className="mt-1 list-inside list-disc">
              {validationErrors.map((err) => (
                <li key={err}>{err}</li>
              ))}
            </ul>
          </div>
        )}

        {message && (
          <p className="rounded-md border border-memo-border bg-memo-surface px-3 py-2 text-sm text-memo-ink">
            {message}
          </p>
        )}

        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => void loadConfig()}
            className="rounded-md border border-memo-border px-3 py-2 text-sm hover:bg-memo-surface"
          >
            다시 불러오기
          </button>
          <button
            type="button"
            onClick={handleFormat}
            className="rounded-md border border-memo-border px-3 py-2 text-sm hover:bg-memo-surface"
          >
            JSON 정렬
          </button>
          <button
            type="button"
            onClick={() => void handleCopy()}
            className="rounded-md border border-memo-border px-3 py-2 text-sm hover:bg-memo-surface"
          >
            복사
          </button>
          <button
            type="button"
            onClick={() => void handleSave()}
            disabled={saving || validationErrors.length > 0}
            className="rounded-md bg-memo-accent px-3 py-2 text-sm font-medium text-white disabled:opacity-50"
          >
            {saving ? "저장 중…" : "GitHub에 저장"}
          </button>
        </div>

        <p className="text-xs text-memo-muted">
          GitHub 저장 후 PC 작업 스케줄러가 <code>git pull</code> 하면 다음 크롤(09:15 KST)부터 반영됩니다.
          Vercel에 <code>GITHUB_TOKEN</code>, <code>GITHUB_REPO</code> 환경 변수가 필요합니다.
        </p>
      </main>
    </div>
  );
}
