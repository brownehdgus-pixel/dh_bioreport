# Supabase로 crawl_config 저장소 이전 (검토)

현재 `data/crawl_config.json` + GitHub Contents API + PC `git pull` 구조를 Supabase 연동 후 아래처럼 바꿀 수 있습니다.

## 현재 vs Supabase

| 항목 | 현재 (JSON + Git) | Supabase 이전 후 |
|------|-------------------|------------------|
| 설정 저장 | GitHub `data/crawl_config.json` | `crawl_config` 테이블 (jsonb) |
| Admin 저장 | GitHub API PUT | Supabase upsert |
| PC 크롤러 | 로컬 파일 + git pull | Supabase REST/SDK fetch |
| Vercel build skip | `crawl_config.json` only | 불필요 (config가 repo 밖) |
| news.json | Git (동일) | Supabase 또는 Git (별도 마이그레이션) |

## 제안 스키마

```sql
create table crawl_config (
  id text primary key default 'default',
  version int not null default 1,
  config jsonb not null,
  updated_at timestamptz not null default now()
);
```

## 마이그레이션 순서 (참고)

1. Supabase 프로젝트 + RLS (service role for crawler, admin session for UI)
2. `scripts/collect_news.py` — `load_crawl_config()`가 Supabase URL/키로 fetch
3. `/api/admin/crawl-config` — GitHub PUT 대신 Supabase upsert
4. `vercel.json` `ignoreCommand` — config-only skip 제거 또는 단순화
5. `run_daily_crawl.bat` — `git pull`은 news.json Git 경로 유지 시에만 필요

## 장점

- Admin 저장 즉시 반영 (git pull 불필요)
- Vercel·PC·크롤러 단일 소스
- 설정 변경 이력(audit) 확장 용이

## 주의

- `news.json`을 Supabase로 옮기기 전까지는 **뉴스 데이터(Git)** 와 **크롤 설정(DB)** 이 이원화됨
- 크롤러 PC에 `SUPABASE_URL` + service key 필요 (`.env.local`)

---

*문서 버전: Phase 8 검토 — 구현 범위 외*
