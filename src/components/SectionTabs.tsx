"use client";

import type { NewsSection, TabId } from "@/data/types";
import { TAB_LABELS } from "@/data/types";

type Props = {
  activeTab: TabId;
  onTabChange: (tab: TabId) => void;
  counts: Record<TabId, number>;
  sections: NewsSection[];
};

export function SectionTabs({ activeTab, onTabChange, counts, sections }: Props) {
  const tabs: TabId[] = ["all", ...sections];

  return (
    <div className="sticky top-0 z-10 border-b border-memo-border bg-memo-bg/95 backdrop-blur-sm">
      <div className="scrollbar-hide flex gap-1 overflow-x-auto px-3 py-2.5">
        {tabs.map((tab) => {
          const isActive = activeTab === tab;
          return (
            <button
              key={tab}
              type="button"
              onClick={() => onTabChange(tab)}
              className={`shrink-0 rounded-full px-3 py-1.5 text-xs font-medium transition-colors ${
                isActive
                  ? "bg-memo-accent text-white shadow-sm"
                  : "bg-memo-surface text-memo-muted ring-1 ring-memo-border hover:text-memo-ink"
              }`}
            >
              {TAB_LABELS[tab]}
              <span
                className={`ml-1 tabular-nums ${
                  isActive ? "text-white/80" : "text-memo-muted/70"
                }`}
              >
                {counts[tab]}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
