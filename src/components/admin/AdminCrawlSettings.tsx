"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import {
  EVENT_BOOST_KEYS,
  EVENT_BOOST_LABELS,
  UI_LIMITS,
  configToFormState,
  defaultEmptyForm,
  formToJsonText,
  newRowId,
  parseAndValidateJsonText,
  validateFormState,
  type CrawlConfigFormState,
} from "@/lib/crawlConfigForm";

const inputClass =
  "w-full rounded-md border border-memo-border bg-memo-bg px-3 py-2 text-sm text-memo-ink outline-none focus:border-memo-accent focus:ring-1 focus:ring-memo-accent/30";

const labelClass = "mb-1 block text-xs font-medium text-memo-ink";

const sectionClass = "rounded-lg border border-memo-border bg-memo-surface p-4 space-y-3";

function SectionTitle({ children }: { children: React.ReactNode }) {
  return <h2 className="text-sm font-semibold text-memo-ink">{children}</h2>;
}

export function AdminCrawlSettings() {
  const [baseConfig, setBaseConfig] = useState<Record<string, unknown> | null>(null);
  const [form, setForm] = useState<CrawlConfigFormState>(defaultEmptyForm());
  const [loadError, setLoadError] = useState("");
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const [message, setMessage] = useState("");
  const [saving, setSaving] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const [advancedOpen, setAdvancedOpen] = useState(false);
  const [advancedJson, setAdvancedJson] = useState("");
  const [useAdvancedJson, setUseAdvancedJson] = useState(false);

  const loadConfig = useCallback(async () => {
    setLoadError("");
    setMessage("");
    try {
      const res = await fetch("/api/admin/crawl-config");
      if (!res.ok) {
        const data = (await res.json()) as { error?: string };
        throw new Error(data.error || `불러오기 실패 (${res.status})`);
      }
      const data = (await res.json()) as { content: string };
      const config = JSON.parse(data.content) as Record<string, unknown>;
      setBaseConfig(config);
      setForm(configToFormState(config));
      setUseAdvancedJson(false);
      setLoaded(true);
    } catch (err) {
      setLoadError(err instanceof Error ? err.message : "설정을 불러오지 못했습니다.");
    }
  }, []);

  useEffect(() => {
    void loadConfig();
  }, [loadConfig]);

  const jsonFromForm = useMemo(() => {
    if (!baseConfig) return "";
    return formToJsonText(baseConfig, form);
  }, [baseConfig, form]);

  useEffect(() => {
    if (!useAdvancedJson) {
      setAdvancedJson(jsonFromForm);
    }
  }, [jsonFromForm, useAdvancedJson]);

  function updateForm(updater: (prev: CrawlConfigFormState) => CrawlConfigFormState) {
    setForm((prev) => updater(prev));
    setMessage("");
    if (!useAdvancedJson) {
      setValidationErrors([]);
    }
  }

  function validateCurrent(): boolean {
    if (useAdvancedJson) {
      const result = parseAndValidateJsonText(advancedJson);
      if (!result.ok) {
        setValidationErrors(result.errors);
        return false;
      }
      setValidationErrors([]);
      return true;
    }
    const errors = validateFormState(form);
    if (errors.length > 0) {
      setValidationErrors(errors);
      return false;
    }
    setValidationErrors([]);
    return true;
  }

  async function handleSave() {
    if (!validateCurrent()) {
      setMessage("저장하기 전에 아래 오류를 수정해 주세요.");
      return;
    }

    let content: string;
    if (useAdvancedJson) {
      content = advancedJson.endsWith("\n") ? advancedJson : `${advancedJson}\n`;
    } else if (baseConfig) {
      content = formToJsonText(baseConfig, form);
    } else {
      setMessage("설정이 아직 불러와지지 않았습니다.");
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
      const data = (await res.json()) as {
        ok?: boolean;
        message?: string;
        error?: string;
        errors?: string[];
      };
      if (!res.ok) {
        if (data.errors?.length) setValidationErrors(data.errors);
        throw new Error(data.error || `저장 실패 (${res.status})`);
      }
      setMessage("GitHub에 반영되었습니다. 다음 자동 크롤링부터 적용됩니다.");
      setUseAdvancedJson(false);
      await loadConfig();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "저장에 실패했습니다.");
    } finally {
      setSaving(false);
    }
  }

  async function handleLogout() {
    await fetch("/api/admin/logout", { method: "POST" });
    window.location.reload();
  }

  function syncAdvancedFromForm() {
    setAdvancedJson(jsonFromForm);
    setUseAdvancedJson(false);
    setValidationErrors([]);
    setMessage("폼 내용을 JSON에 반영했습니다.");
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
        <p className="mt-2 rounded-md border border-blue-100 bg-blue-50 px-3 py-2 text-sm text-blue-900">
          이 설정은 <strong>다음 자동 크롤링부터</strong> 적용됩니다.
          <br />
          저장 후 PC 크롤러가 <strong>09:30</strong> 실행 시 git pull로 최신 설정을 반영합니다.
        </p>
      </header>

      <main className="space-y-5 px-4 py-6">
        {loadError && (
          <p className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
            {loadError}
          </p>
        )}

        {!loaded && !loadError && (
          <p className="text-sm text-memo-muted">설정 불러오는 중…</p>
        )}

        {loaded && (
          <>
            {/* 수집 한도 */}
            <section className={sectionClass}>
              <SectionTitle>수집 한도</SectionTitle>
              <p className="text-xs text-memo-muted">
                며칠 이내 기사만 모을지, 하루 리포트에 몇 개까지 넣을지 정합니다.
              </p>
              <div className="grid gap-3 sm:grid-cols-3">
                <div>
                  <label className={labelClass}>
                    {UI_LIMITS.maxItemAgeDays.label} ({UI_LIMITS.maxItemAgeDays.min}~
                    {UI_LIMITS.maxItemAgeDays.max})
                  </label>
                  <input
                    type="number"
                    className={inputClass}
                    min={UI_LIMITS.maxItemAgeDays.min}
                    max={UI_LIMITS.maxItemAgeDays.max}
                    value={form.maxItemAgeDays}
                    onChange={(e) =>
                      updateForm((p) => ({
                        ...p,
                        maxItemAgeDays: Number(e.target.value),
                      }))
                    }
                  />
                </div>
                <div>
                  <label className={labelClass}>
                    {UI_LIMITS.maxItemsInReport.label} ({UI_LIMITS.maxItemsInReport.min}~
                    {UI_LIMITS.maxItemsInReport.max})
                  </label>
                  <input
                    type="number"
                    className={inputClass}
                    min={UI_LIMITS.maxItemsInReport.min}
                    max={UI_LIMITS.maxItemsInReport.max}
                    value={form.maxItemsInReport}
                    onChange={(e) =>
                      updateForm((p) => ({
                        ...p,
                        maxItemsInReport: Number(e.target.value),
                      }))
                    }
                  />
                </div>
                <div>
                  <label className={labelClass}>
                    {UI_LIMITS.maxSummaryLines.label} ({UI_LIMITS.maxSummaryLines.min}~
                    {UI_LIMITS.maxSummaryLines.max})
                  </label>
                  <input
                    type="number"
                    className={inputClass}
                    min={UI_LIMITS.maxSummaryLines.min}
                    max={UI_LIMITS.maxSummaryLines.max}
                    value={form.maxSummaryLines}
                    onChange={(e) =>
                      updateForm((p) => ({
                        ...p,
                        maxSummaryLines: Number(e.target.value),
                      }))
                    }
                  />
                </div>
              </div>
            </section>

            {/* 과거 리포트 중복 제외 */}
            <section className={sectionClass}>
              <SectionTitle>과거 리포트 중복 제외</SectionTitle>
              <p className="text-xs text-memo-muted">
                이미 지난 날짜 리포트에 실린 기사는 오늘 리포트 후보에서 제외합니다. 같은 날 다시
                실행할 때는 오늘 리포트는 비교 대상에서 빠집니다.
              </p>
              <div className="space-y-2">
                <label className="flex items-center gap-2 text-sm text-memo-ink">
                  <input
                    type="checkbox"
                    checked={form.excludePreviouslyReported}
                    onChange={(e) =>
                      updateForm((p) => ({
                        ...p,
                        excludePreviouslyReported: e.target.checked,
                      }))
                    }
                  />
                  과거 리포트에 이미 실린 뉴스 제외
                </label>
                <label className="flex items-center gap-2 text-sm text-memo-ink">
                  <input
                    type="checkbox"
                    checked={form.excludeSameUrl}
                    disabled={!form.excludePreviouslyReported}
                    onChange={(e) =>
                      updateForm((p) => ({ ...p, excludeSameUrl: e.target.checked }))
                    }
                  />
                  동일 URL 제외
                </label>
                <label className="flex items-center gap-2 text-sm text-memo-ink">
                  <input
                    type="checkbox"
                    checked={form.excludeSameTitle}
                    disabled={!form.excludePreviouslyReported}
                    onChange={(e) =>
                      updateForm((p) => ({ ...p, excludeSameTitle: e.target.checked }))
                    }
                  />
                  동일 제목 제외
                </label>
              </div>
            </section>

            {/* Google News */}
            <section className={sectionClass}>
              <SectionTitle>Google News 검색 키워드</SectionTitle>
              <p className="text-xs text-memo-muted">
                Google News RSS로 검색할 영문 키워드입니다. 체크 해제하면 해당 검색은 건너뜁니다.
              </p>
              <div className="space-y-2">
                {form.googleQueries.map((row, index) => (
                  <div key={row.id} className="flex flex-wrap items-center gap-2">
                    <input
                      type="text"
                      className={`${inputClass} min-w-[200px] flex-1`}
                      placeholder="예: biotech FDA approval"
                      value={row.query}
                      onChange={(e) =>
                        updateForm((p) => {
                          const next = [...p.googleQueries];
                          next[index] = { ...next[index], query: e.target.value };
                          return { ...p, googleQueries: next };
                        })
                      }
                    />
                    <label className="flex items-center gap-1 text-xs text-memo-ink">
                      <input
                        type="checkbox"
                        checked={row.enabled}
                        onChange={(e) =>
                          updateForm((p) => {
                            const next = [...p.googleQueries];
                            next[index] = { ...next[index], enabled: e.target.checked };
                            return { ...p, googleQueries: next };
                          })
                        }
                      />
                      사용
                    </label>
                    <button
                      type="button"
                      className="rounded border border-memo-border px-2 py-1 text-xs text-red-700 hover:bg-red-50"
                      onClick={() =>
                        updateForm((p) => ({
                          ...p,
                          googleQueries: p.googleQueries.filter((_, i) => i !== index),
                        }))
                      }
                    >
                      삭제
                    </button>
                  </div>
                ))}
              </div>
              <button
                type="button"
                className="rounded-md border border-memo-border px-3 py-1.5 text-xs hover:bg-memo-bg"
                onClick={() =>
                  updateForm((p) => ({
                    ...p,
                    googleQueries: [...p.googleQueries, { id: newRowId(), query: "", enabled: true }],
                  }))
                }
              >
                + 검색어 추가
              </button>
            </section>

            {/* RSS */}
            <section className={sectionClass}>
              <SectionTitle>RSS 피드</SectionTitle>
              <p className="text-xs text-memo-muted">
                RSS 주소는 http:// 또는 https:// 로 시작해야 합니다.
              </p>
              <div className="space-y-3">
                {form.rssFeeds.map((row, index) => (
                  <div key={row.id} className="space-y-2 rounded border border-memo-border/60 p-3">
                    <div className="flex flex-wrap gap-2">
                      <div className="min-w-[140px] flex-1">
                        <label className={labelClass}>이름</label>
                        <input
                          type="text"
                          className={inputClass}
                          value={row.name}
                          onChange={(e) =>
                            updateForm((p) => {
                              const next = [...p.rssFeeds];
                              next[index] = { ...next[index], name: e.target.value };
                              return { ...p, rssFeeds: next };
                            })
                          }
                        />
                      </div>
                      <div className="min-w-[200px] flex-[2]">
                        <label className={labelClass}>URL</label>
                        <input
                          type="url"
                          className={inputClass}
                          placeholder="https://..."
                          value={row.url}
                          onChange={(e) =>
                            updateForm((p) => {
                              const next = [...p.rssFeeds];
                              next[index] = { ...next[index], url: e.target.value };
                              return { ...p, rssFeeds: next };
                            })
                          }
                        />
                      </div>
                    </div>
                    <div className="flex items-center justify-between">
                      <label className="flex items-center gap-1 text-xs text-memo-ink">
                        <input
                          type="checkbox"
                          checked={row.enabled}
                          onChange={(e) =>
                            updateForm((p) => {
                              const next = [...p.rssFeeds];
                              next[index] = { ...next[index], enabled: e.target.checked };
                              return { ...p, rssFeeds: next };
                            })
                          }
                        />
                        사용
                      </label>
                      <button
                        type="button"
                        className="rounded border border-memo-border px-2 py-1 text-xs text-red-700 hover:bg-red-50"
                        onClick={() =>
                          updateForm((p) => ({
                            ...p,
                            rssFeeds: p.rssFeeds.filter((_, i) => i !== index),
                          }))
                        }
                      >
                        삭제
                      </button>
                    </div>
                  </div>
                ))}
              </div>
              <button
                type="button"
                className="rounded-md border border-memo-border px-3 py-1.5 text-xs hover:bg-memo-bg"
                onClick={() =>
                  updateForm((p) => ({
                    ...p,
                    rssFeeds: [
                      ...p.rssFeeds,
                      { id: newRowId(), name: "", url: "", enabled: true },
                    ],
                  }))
                }
              >
                + RSS 피드 추가
              </button>
            </section>

            {/* 제외 키워드 */}
            <section className={sectionClass}>
              <SectionTitle>제외 키워드</SectionTitle>
              <p className="text-xs text-memo-muted">
                제목·요약에 아래 단어가 포함된 기사는 리포트에서 빼 줍니다. 예: market size, 건강상식,
                병원홍보
              </p>
              <div className="space-y-2">
                {form.excludeKeywords.map((kw, index) => (
                  <div key={`ex-${index}`} className="flex gap-2">
                    <input
                      type="text"
                      className={inputClass}
                      value={kw}
                      onChange={(e) =>
                        updateForm((p) => {
                          const next = [...p.excludeKeywords];
                          next[index] = e.target.value;
                          return { ...p, excludeKeywords: next };
                        })
                      }
                    />
                    <button
                      type="button"
                      className="shrink-0 rounded border border-memo-border px-2 py-1 text-xs text-red-700 hover:bg-red-50"
                      onClick={() =>
                        updateForm((p) => ({
                          ...p,
                          excludeKeywords: p.excludeKeywords.filter((_, i) => i !== index),
                        }))
                      }
                    >
                      삭제
                    </button>
                  </div>
                ))}
              </div>
              <button
                type="button"
                className="rounded-md border border-memo-border px-3 py-1.5 text-xs hover:bg-memo-bg"
                onClick={() =>
                  updateForm((p) => ({
                    ...p,
                    excludeKeywords: [...p.excludeKeywords, ""],
                  }))
                }
              >
                + 키워드 추가
              </button>
            </section>

            {/* 이벤트 가중치 */}
            <section className={sectionClass}>
              <SectionTitle>이벤트 유형별 가중치</SectionTitle>
              <p className="text-xs text-memo-muted">
                숫자가 클수록 리포트 상단에 올라갈 가능성이 높습니다. (-5 ~ 5)
              </p>
              <div className="grid gap-3 sm:grid-cols-2">
                {EVENT_BOOST_KEYS.map((key) => (
                  <div key={key}>
                    <label className={labelClass}>{EVENT_BOOST_LABELS[key]}</label>
                    <input
                      type="number"
                      className={inputClass}
                      min={-5}
                      max={5}
                      value={form.eventTypeBoosts[key]}
                      onChange={(e) =>
                        updateForm((p) => ({
                          ...p,
                          eventTypeBoosts: {
                            ...p.eventTypeBoosts,
                            [key]: Number(e.target.value),
                          },
                        }))
                      }
                    />
                  </div>
                ))}
              </div>
            </section>

            {/* 키워드 가중치 */}
            <section className={sectionClass}>
              <SectionTitle>키워드 가중치</SectionTitle>
              <p className="text-xs text-memo-muted">
                키워드는 쉼표(,)로 구분합니다. 제목·요약에 포함되면 boost만큼 점수가 올라갑니다.
              </p>
              <div className="space-y-2">
                {form.keywordBoosts.map((row, index) => (
                  <div key={row.id} className="flex flex-wrap items-end gap-2">
                    <div className="min-w-[200px] flex-1">
                      <label className={labelClass}>키워드 (쉼표 구분)</label>
                      <input
                        type="text"
                        className={inputClass}
                        placeholder="fda, phase 3, merger"
                        value={row.keywordsText}
                        onChange={(e) =>
                          updateForm((p) => {
                            const next = [...p.keywordBoosts];
                            next[index] = { ...next[index], keywordsText: e.target.value };
                            return { ...p, keywordBoosts: next };
                          })
                        }
                      />
                    </div>
                    <div className="w-24">
                      <label className={labelClass}>boost</label>
                      <input
                        type="number"
                        className={inputClass}
                        min={-5}
                        max={5}
                        value={row.boost}
                        onChange={(e) =>
                          updateForm((p) => {
                            const next = [...p.keywordBoosts];
                            next[index] = { ...next[index], boost: Number(e.target.value) };
                            return { ...p, keywordBoosts: next };
                          })
                        }
                      />
                    </div>
                    <button
                      type="button"
                      className="rounded border border-memo-border px-2 py-2 text-xs text-red-700 hover:bg-red-50"
                      onClick={() =>
                        updateForm((p) => ({
                          ...p,
                          keywordBoosts: p.keywordBoosts.filter((_, i) => i !== index),
                        }))
                      }
                    >
                      삭제
                    </button>
                  </div>
                ))}
              </div>
              <button
                type="button"
                className="rounded-md border border-memo-border px-3 py-1.5 text-xs hover:bg-memo-bg"
                onClick={() =>
                  updateForm((p) => ({
                    ...p,
                    keywordBoosts: [
                      ...p.keywordBoosts,
                      { id: newRowId(), keywordsText: "", boost: 1 },
                    ],
                  }))
                }
              >
                + 키워드 그룹 추가
              </button>
            </section>

            {/* 섹션 / 이벤트 분류 키워드 */}
            <section className={sectionClass}>
              <SectionTitle>섹션 분류 키워드</SectionTitle>
              <p className="text-xs text-memo-muted">
                위에서 아래 순서대로 우선 매칭됩니다. 키워드는 쉼표(,)로 구분합니다.
              </p>
              <div className="space-y-3">
                {form.sectionKeywords.map((row, index) => (
                  <div key={row.id}>
                    <label className={labelClass}>{row.id}</label>
                    <textarea
                      className={`${inputClass} min-h-[60px] text-xs`}
                      value={row.keywordsText}
                      onChange={(e) =>
                        updateForm((p) => {
                          const next = [...p.sectionKeywords];
                          next[index] = { ...next[index], keywordsText: e.target.value };
                          return { ...p, sectionKeywords: next };
                        })
                      }
                    />
                  </div>
                ))}
              </div>
            </section>

            <section className={sectionClass}>
              <SectionTitle>이벤트 유형(eventType) 분류 키워드</SectionTitle>
              <p className="text-xs text-memo-muted">
                위에서 아래 순서대로 우선 매칭됩니다. 키워드는 쉼표(,)로 구분합니다.
              </p>
              <div className="space-y-3">
                {form.eventTypeKeywords.map((row, index) => (
                  <div key={row.id}>
                    <label className={labelClass}>{row.id}</label>
                    <textarea
                      className={`${inputClass} min-h-[60px] text-xs`}
                      value={row.keywordsText}
                      onChange={(e) =>
                        updateForm((p) => {
                          const next = [...p.eventTypeKeywords];
                          next[index] = { ...next[index], keywordsText: e.target.value };
                          return { ...p, eventTypeKeywords: next };
                        })
                      }
                    />
                  </div>
                ))}
              </div>
            </section>

            {/* 고급 JSON */}
            <details
              className={sectionClass}
              open={advancedOpen}
              onToggle={(e) => setAdvancedOpen((e.target as HTMLDetailsElement).open)}
            >
              <summary className="cursor-pointer text-sm font-semibold text-memo-ink">
                고급 JSON 보기/편집
              </summary>
              <div className="mt-3 space-y-2">
                <label className="flex items-center gap-2 text-xs text-memo-ink">
                  <input
                    type="checkbox"
                    checked={useAdvancedJson}
                    onChange={(e) => setUseAdvancedJson(e.target.checked)}
                  />
                  JSON을 직접 수정하여 저장 (체크 시 아래 내용이 저장됩니다)
                </label>
                <textarea
                  className="min-h-[320px] w-full rounded-md border border-memo-border bg-memo-bg px-3 py-2 font-mono text-xs text-memo-ink outline-none focus:border-memo-accent"
                  value={advancedJson}
                  onChange={(e) => {
                    setAdvancedJson(e.target.value);
                    setUseAdvancedJson(true);
                    setMessage("");
                  }}
                  spellCheck={false}
                />
                <button
                  type="button"
                  className="rounded-md border border-memo-border px-3 py-1.5 text-xs hover:bg-memo-bg"
                  onClick={syncAdvancedFromForm}
                >
                  위 폼 내용을 JSON에 반영
                </button>
              </div>
            </details>
          </>
        )}

        {validationErrors.length > 0 && (
          <div className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900">
            <p className="font-medium">확인해 주세요</p>
            <ul className="mt-1 list-inside list-disc">
              {validationErrors.map((err) => (
                <li key={err}>{err}</li>
              ))}
            </ul>
          </div>
        )}

        {message && (
          <p
            className={`rounded-md border px-3 py-2 text-sm ${
              message.includes("반영되었습니다")
                ? "border-green-200 bg-green-50 text-green-900"
                : "border-memo-border bg-memo-surface text-memo-ink"
            }`}
          >
            {message}
          </p>
        )}

        <div className="flex flex-wrap gap-2 pb-8">
          <button
            type="button"
            onClick={() => void loadConfig()}
            className="rounded-md border border-memo-border px-3 py-2 text-sm hover:bg-memo-surface"
          >
            다시 불러오기
          </button>
          <button
            type="button"
            onClick={() => void handleSave()}
            disabled={saving || !loaded}
            className="rounded-md bg-memo-accent px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
          >
            {saving ? "저장 중…" : "GitHub에 저장"}
          </button>
        </div>
      </main>
    </div>
  );
}
