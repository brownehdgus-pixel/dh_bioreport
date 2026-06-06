"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { NewsCard } from "@/components/NewsCard";
import type { NewsItem } from "@/data/types";
import { NEWS_SECTIONS, SECTION_LABELS } from "@/data/types";
import {
  createItemId,
  draftToNewsItem,
  draftToPreviewItem,
  emptyDraft,
  itemsToJson,
  type NewsItemDraft,
} from "@/lib/adminNews";

const inputClass =
  "w-full rounded-md border border-memo-border bg-memo-bg px-3 py-2 text-sm text-memo-ink outline-none focus:border-memo-accent focus:ring-1 focus:ring-memo-accent/30";

const labelClass = "mb-1 block text-xs font-medium text-memo-ink";

export function AdminPanel() {
  const [draft, setDraft] = useState<NewsItemDraft>(emptyDraft);
  const [items, setItems] = useState<NewsItem[]>([]);
  const [copyMessage, setCopyMessage] = useState("");
  const [formError, setFormError] = useState("");

  const previewItem = useMemo(() => draftToPreviewItem(draft), [draft]);
  const jsonOutput = useMemo(() => itemsToJson(items), [items]);

  function updateDraft<K extends keyof NewsItemDraft>(key: K, value: NewsItemDraft[K]) {
    setDraft((prev) => ({ ...prev, [key]: value }));
    setFormError("");
  }

  function handleAddItem() {
    const item = draftToNewsItem(draft, createItemId());
    if (!item) {
      setFormError("제목, 출처, 날짜는 꼭 입력해 주세요.");
      return;
    }
    setItems((prev) => [...prev, item]);
    setDraft(emptyDraft());
    setFormError("");
  }

  function handleRemoveItem(id: string) {
    setItems((prev) => prev.filter((item) => item.id !== id));
  }

  async function handleCopyJson() {
    if (items.length === 0) {
      setCopyMessage("복사할 뉴스가 없습니다. 먼저 「목록에 추가」를 눌러 주세요.");
      return;
    }
    try {
      await navigator.clipboard.writeText(jsonOutput);
      setCopyMessage("복사 완료! 아래 안내대로 news.json에 붙여넣으세요.");
    } catch {
      setCopyMessage("복사에 실패했습니다. 아래 JSON을 직접 드래그해서 복사해 주세요.");
    }
  }

  function handleClearList() {
    if (items.length === 0) return;
    if (window.confirm("추가한 뉴스 목록을 모두 지울까요?")) {
      setItems([]);
      setCopyMessage("");
    }
  }

  async function handleLogout() {
    await fetch("/api/admin/logout", { method: "POST" });
    window.location.reload();
  }

  return (
    <div className="mx-auto min-h-dvh max-w-lg">
      <header className="border-b border-memo-border bg-memo-surface px-4 pb-5 pt-6">
        <div className="mb-3 flex items-center justify-between gap-2">
          <Link
            href="/reports"
            className="inline-flex items-center gap-1 text-xs font-medium text-memo-accent"
          >
            ← 리포트 목록으로
          </Link>
          <div className="flex items-center gap-3">
            <Link
              href="/admin/crawl-settings"
              className="text-xs font-medium text-memo-accent"
            >
              크롤 설정
            </Link>
            <button
              type="button"
              onClick={handleLogout}
              className="text-xs text-memo-muted underline"
            >
              로그아웃
            </button>
          </div>
        </div>
        <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-memo-accent">
          관리자 도구
        </p>
        <h1 className="mt-1 font-serif text-xl font-semibold text-memo-ink">뉴스 입력 · 미리보기</h1>
        <p className="mt-2 text-[13px] leading-relaxed text-memo-muted">
          뉴스를 입력하고 카드 모양을 확인한 뒤, 여러 건을 모아 JSON으로 복사할 수 있습니다.
          아직 저장(DB) 기능은 없으며, 복사한 내용을{" "}
          <code className="rounded bg-memo-bg px-1 text-[12px]">data/news.json</code> 파일에 직접
          붙여넣어 주세요.
        </p>
      </header>

      <div className="space-y-6 px-4 py-5">
        <section className="rounded-xl border border-memo-border bg-memo-surface p-4">
          <h2 className="mb-1 font-serif text-base font-semibold text-memo-ink">1. 뉴스 내용 입력</h2>
          <p className="mb-4 text-[12px] text-memo-muted">
            한 건씩 작성한 뒤 「목록에 추가」를 누르면 아래 목록에 쌓입니다.
          </p>

          <div className="space-y-3">
            <div>
              <label className={labelClass}>제목 *</label>
              <input
                className={inputClass}
                value={draft.title}
                onChange={(e) => updateDraft("title", e.target.value)}
                placeholder="예: FDA, ADC 후보물질 BTD 검토 착수"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className={labelClass}>출처 *</label>
                <input
                  className={inputClass}
                  value={draft.source}
                  onChange={(e) => updateDraft("source", e.target.value)}
                  placeholder="예: Endpoints News"
                />
              </div>
              <div>
                <label className={labelClass}>날짜 *</label>
                <input
                  type="date"
                  className={inputClass}
                  value={draft.date}
                  onChange={(e) => updateDraft("date", e.target.value)}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className={labelClass}>섹션</label>
                <select
                  className={inputClass}
                  value={draft.section}
                  onChange={(e) => updateDraft("section", e.target.value as NewsItemDraft["section"])}
                >
                  {NEWS_SECTIONS.map((s) => (
                    <option key={s} value={s}>
                      {SECTION_LABELS[s]}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className={labelClass}>이벤트 유형</label>
                <input
                  className={inputClass}
                  value={draft.eventType}
                  onChange={(e) => updateDraft("eventType", e.target.value)}
                  placeholder="예: regulatory, funding"
                />
              </div>
            </div>

            <div>
              <label className={labelClass}>요약</label>
              <textarea
                className={`${inputClass} min-h-[80px] resize-y`}
                value={draft.summary}
                onChange={(e) => updateDraft("summary", e.target.value)}
                placeholder="기사 내용을 2~3문장으로 요약"
              />
            </div>

            <div>
              <label className={labelClass}>의미 (분석 메모)</label>
              <textarea
                className={`${inputClass} min-h-[80px] resize-y`}
                value={draft.significance}
                onChange={(e) => updateDraft("significance", e.target.value)}
                placeholder="우리에게 왜 중요한지, 업계 영향"
              />
            </div>

            <div>
              <label className={labelClass}>키워드</label>
              <input
                className={inputClass}
                value={draft.keywordsText}
                onChange={(e) => updateDraft("keywordsText", e.target.value)}
                placeholder="쉼표로 구분 (예: ADC, FDA, Oncology)"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className={labelClass}>중요도 점수 (1~10)</label>
                <input
                  type="number"
                  min={1}
                  max={10}
                  className={inputClass}
                  value={draft.importanceScore}
                  onChange={(e) => updateDraft("importanceScore", e.target.value)}
                />
              </div>
              <div>
                <label className={labelClass}>국내 연관 점수 (1~10)</label>
                <input
                  type="number"
                  min={1}
                  max={10}
                  className={inputClass}
                  value={draft.koreaRelevanceScore}
                  onChange={(e) => updateDraft("koreaRelevanceScore", e.target.value)}
                />
              </div>
            </div>

            <div>
              <label className={labelClass}>원문 URL</label>
              <input
                type="url"
                className={inputClass}
                value={draft.url}
                onChange={(e) => updateDraft("url", e.target.value)}
                placeholder="https://..."
              />
            </div>
          </div>

          {formError && (
            <p className="mt-3 text-[12px] font-medium text-red-600" role="alert">
              {formError}
            </p>
          )}

          <div className="mt-4 flex flex-wrap gap-2">
            <button
              type="button"
              onClick={handleAddItem}
              className="rounded-md bg-memo-accent px-4 py-2.5 text-sm font-medium text-white active:bg-memo-accent/90"
            >
              목록에 추가
            </button>
            <button
              type="button"
              onClick={() => {
                setDraft(emptyDraft());
                setFormError("");
              }}
              className="rounded-md border border-memo-border bg-memo-bg px-4 py-2.5 text-sm text-memo-ink"
            >
              입력 칸 비우기
            </button>
          </div>
        </section>

        <section>
          <h2 className="mb-1 font-serif text-base font-semibold text-memo-ink">2. 카드 미리보기</h2>
          <p className="mb-3 text-[12px] text-memo-muted">
            지금 입력 중인 내용이 실제 화면과 같은 모양으로 보입니다.
          </p>
          <NewsCard item={previewItem} />
        </section>

        <section className="rounded-xl border border-memo-border bg-memo-surface p-4">
          <div className="mb-3 flex items-center justify-between gap-2">
            <div>
              <h2 className="font-serif text-base font-semibold text-memo-ink">
                3. 추가한 뉴스 ({items.length}건)
              </h2>
              <p className="text-[12px] text-memo-muted">여러 건을 추가한 뒤 JSON을 복사하세요.</p>
            </div>
            {items.length > 0 && (
              <button
                type="button"
                onClick={handleClearList}
                className="shrink-0 text-[12px] text-memo-muted underline"
              >
                전체 삭제
              </button>
            )}
          </div>

          {items.length === 0 ? (
            <p className="py-6 text-center text-sm text-memo-muted">
              아직 추가된 뉴스가 없습니다.
            </p>
          ) : (
            <ul className="space-y-3">
              {items.map((item, index) => (
                <li
                  key={item.id}
                  className="flex items-start justify-between gap-3 rounded-lg border border-memo-border bg-memo-bg p-3"
                >
                  <div className="min-w-0 flex-1">
                    <p className="text-[11px] text-memo-muted">
                      {index + 1}번 · {SECTION_LABELS[item.section]} · {item.source}
                    </p>
                    <p className="mt-0.5 truncate text-sm font-medium text-memo-ink">
                      {item.title}
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => handleRemoveItem(item.id)}
                    className="shrink-0 rounded border border-memo-border px-2 py-1 text-[11px] text-memo-muted"
                  >
                    삭제
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="rounded-xl border border-memo-accent/30 bg-memo-accentLight/30 p-4">
          <h2 className="mb-1 font-serif text-base font-semibold text-memo-ink">
            4. JSON 복사 (news.json용)
          </h2>
          <ol className="mb-4 list-decimal space-y-1 pl-4 text-[12px] leading-relaxed text-memo-muted">
            <li>아래 「JSON 복사하기」 버튼을 누릅니다.</li>
            <li>
              프로젝트의 <strong className="text-memo-ink">data/news.json</strong> 파일을 엽니다.
            </li>
            <li>
              붙이고 싶은 날짜 리포트 안의 <strong className="text-memo-ink">items</strong> 배열
              [ ... ] 안에, 기존 항목 뒤에 쉼표(,)를 붙이고 붙여넣습니다.
            </li>
            <li>파일을 저장한 뒤, 앱을 새로고침하면 반영됩니다.</li>
          </ol>

          <button
            type="button"
            onClick={handleCopyJson}
            disabled={items.length === 0}
            className="w-full rounded-md bg-memo-accent px-4 py-3 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-50"
          >
            JSON 복사하기
          </button>

          {copyMessage && (
            <p className="mt-2 text-[12px] font-medium text-memo-accent" role="status">
              {copyMessage}
            </p>
          )}

          <label className={`${labelClass} mt-4`}>복사할 JSON 내용</label>
          <textarea
            readOnly
            className={`${inputClass} min-h-[200px] font-mono text-[11px] leading-relaxed`}
            value={items.length > 0 ? jsonOutput : "뉴스를 추가하면 여기에 JSON이 표시됩니다."}
            onFocus={(e) => items.length > 0 && e.target.select()}
          />
        </section>
      </div>

      <footer className="border-t border-memo-border px-4 py-6 text-center text-[11px] text-memo-muted">
        관리자 입력 · DB 미연결 · 로컬 JSON용
      </footer>
    </div>
  );
}
