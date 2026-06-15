"use client";

import { useMemo, useState } from "react";
import type { DailyReport, NewsItem, TabId } from "@/data/types";
import { itemOrigin } from "@/data/types";
import { BriefingSection } from "./BriefingSection";
import { NewsCard } from "./NewsCard";
import { SectionTabs } from "./SectionTabs";

type Props = {
  report: DailyReport;
};

function filterByTab(items: NewsItem[], tab: TabId) {
  if (tab === "all") return items;
  if (tab === "domestic") return items.filter((item) => itemOrigin(item) === "domestic");
  if (tab === "global") return items.filter((item) => itemOrigin(item) === "global");
  return items.filter((item) => item.section === tab);
}

function buildCounts(items: NewsItem[]) {
  const counts: Record<TabId, number> = {
    all: items.length,
    domestic: 0,
    global: 0,
    regulatory: 0,
    deal: 0,
    modality: 0,
    paper: 0,
    general: 0,
  };
  for (const item of items) {
    counts[itemOrigin(item)]++;
    if (item.section in counts && item.section !== "domestic" && item.section !== "global") {
      counts[item.section]++;
    }
  }
  return counts;
}

export function NewsFeed({ report }: Props) {
  const [activeTab, setActiveTab] = useState<TabId>("all");
  const counts = useMemo(() => buildCounts(report.items), [report.items]);
  const filtered = useMemo(
    () => filterByTab(report.items, activeTab),
    [report.items, activeTab]
  );

  return (
    <div className="mx-auto min-h-dvh max-w-lg">
      <BriefingSection report={report} />
      <SectionTabs
        activeTab={activeTab}
        onTabChange={setActiveTab}
        counts={counts}
        sections={report.sections}
      />

      <main className="px-4 py-4">
        <p className="mb-3 text-xs text-memo-muted">
          {filtered.length}건 · {activeTab === "all" ? "전체 섹션" : "필터 적용"}
        </p>

        <ul className="space-y-4">
          {filtered.map((item) => (
            <li key={item.id}>
              <NewsCard item={item} />
            </li>
          ))}
        </ul>

        {filtered.length === 0 && (
          <p className="py-12 text-center text-sm text-memo-muted">
            해당 섹션에 표시할 뉴스가 없습니다.
          </p>
        )}
      </main>

      <footer className="border-t border-memo-border px-4 py-6 text-center text-[11px] text-memo-muted">
        Daily Bio · v2
      </footer>
    </div>
  );
}
