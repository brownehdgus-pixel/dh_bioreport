"use client";

import { useState } from "react";
import Link from "next/link";

type Props = {
  configMissing: boolean;
};

export function AdminLogin({ configMissing }: Props) {
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const res = await fetch("/api/admin/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password }),
      });
      const data = await res.json();

      if (!res.ok) {
        setError(data.error ?? "로그인에 실패했습니다.");
        return;
      }

      window.location.reload();
    } catch {
      setError("연결에 실패했습니다. 잠시 후 다시 시도해 주세요.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto flex min-h-dvh max-w-lg flex-col">
      <header className="border-b border-memo-border bg-memo-surface px-4 pb-5 pt-6">
        <Link
          href="/reports"
          className="mb-3 inline-flex items-center gap-1 text-xs font-medium text-memo-accent"
        >
          ← 리포트 목록으로
        </Link>
        <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-memo-accent">
          관리자 도구
        </p>
        <h1 className="mt-1 font-serif text-xl font-semibold text-memo-ink">관리자 로그인</h1>
        <p className="mt-2 text-[13px] leading-relaxed text-memo-muted">
          뉴스 입력 화면은 관리자만 들어갈 수 있습니다. 비밀번호를 입력해 주세요.
        </p>
      </header>

      <main className="flex flex-1 flex-col px-4 py-6">
        {configMissing ? (
          <div
            className="mb-4 rounded-lg border border-amber-200 bg-amber-50 p-4 text-[13px] leading-relaxed text-amber-900"
            role="alert"
          >
            <p className="font-semibold">비밀번호가 아직 설정되지 않았습니다</p>
            <p className="mt-2">
              프로젝트 폴더에 <strong>.env.local</strong> 파일을 만들고{" "}
              <code className="rounded bg-white/80 px-1">ADMIN_PASSWORD=원하는비밀번호</code> 를
              적은 뒤, 개발 서버를 다시 시작해 주세요.
            </p>
          </div>
        ) : null}

        <form onSubmit={handleSubmit} className="rounded-xl border border-memo-border bg-memo-surface p-4">
          <label htmlFor="admin-password" className="mb-1 block text-xs font-medium text-memo-ink">
            관리자 비밀번호
          </label>
          <input
            id="admin-password"
            type="password"
            autoComplete="current-password"
            className="w-full rounded-md border border-memo-border bg-memo-bg px-3 py-2.5 text-sm text-memo-ink outline-none focus:border-memo-accent focus:ring-1 focus:ring-memo-accent/30"
            value={password}
            onChange={(e) => {
              setPassword(e.target.value);
              setError("");
            }}
            placeholder="비밀번호 입력"
            disabled={configMissing || loading}
          />

          {error && (
            <p className="mt-3 text-[13px] font-medium text-red-600" role="alert">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={configMissing || loading || !password}
            className="mt-4 w-full rounded-md bg-memo-accent px-4 py-3 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loading ? "확인 중…" : "로그인"}
          </button>
        </form>
      </main>
    </div>
  );
}
