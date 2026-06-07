# LLM 검토용 제시 파일 가이드

다른 LLM에게 **지금까지 반영된 작업 제안 전체**를 검토받을 때, 아래 파일 세트를 제시하면 아키텍처·자동화·보안·데이터 흐름을 한 번에 파악할 수 있습니다.

> 복사용 경로 목록: [`llm_review_manifest.txt`](llm_review_manifest.txt)

```mermaid
flowchart LR
  subgraph pc [Windows_PC]
    bat[run_daily_crawl.bat]
    crawl[collect_news.py]
    push[push_and_notify.py]
    notify[notify_deploy.py]
    bat --> crawl --> push --> notify
  end
  subgraph remote [Remote]
    gh[GitHub]
    vercel[Vercel]
    phone[ntfy_app]
  end
  push --> gh --> vercel
  notify --> phone
  subgraph web [Next.js]
    json[data/news.json]
    reports[getReports.ts]
    admin[/admin]
  end
  crawl --> json
  json --> reports
```

---

## 1. 필수 — 자동화·크롤·배포 파이프라인 (10개)

| 파일 | 검토 포인트 |
|------|-------------|
| `scripts/collect_news.py` | RSS 수집, dedup, `news.json` 병합, Google Translate, 90일 retention |
| `scripts/google_translate.py` | 번역 로직 (`deep-translator`) |
| `scripts/translate_news_summaries.py` | 기존 JSON 일괄 번역 |
| `scripts/env_local.py` | `.env.local` 로드 (크롤/알림용) |
| `scripts/push_and_notify.py` | 변경 시 git commit/push → ntfy 호출 |
| `scripts/notify_deploy.py` | ntfy/Telegram, (선택) Vercel READY 대기 |
| `scripts/run_daily_crawl.bat` | 작업 스케줄러 진입점 (크롤 → push/notify) |
| `scripts/test_daily_crawl.bat` | 수동 테스트 래퍼 |
| `scripts/log_stamp.py` | 로그 날짜/시간 스탬프 |
| `requirements.txt` | Python 의존성 (`feedparser`, `deep-translator`) |

---

## 2. 필수 — 문서·운영 설정 (4개)

| 파일 | 검토 포인트 |
|------|-------------|
| `README.md` | 전체 구조, 크롤·번역·90일·Windows 09:30 KST 흐름 요약 |
| `docs/windows_task_scheduler_setup.md` | 권장 운영 방식 (09:30, push, ntfy, `.env.local`) |
| `docs/github_actions_setup.md` | GitHub Actions 일일 크롤 중단 안내 |
| `.env.local.example` | 필요한 환경 변수 샘플 (비밀값 없음) |

**참고:** `.github/workflows/daily-crawl.yml` 은 **삭제됨**. 없는 것이 정상입니다.

---

## 3. 권장 — 웹앱·데이터·관리자 (8개)

| 파일 | 검토 포인트 |
|------|-------------|
| `src/lib/getReports.ts` | `data/news.json` 단일 소스, 런타임 번역 제거 |
| `src/data/types.ts` | 리포트/아이템 JSON 스키마 |
| `src/lib/adminAuth.ts` | `/admin` 세션·비밀번호 검증 |
| `src/app/api/admin/login/route.ts` | 로그인 API |
| `src/app/api/admin/logout/route.ts` | 로그아웃 API |
| `src/app/admin/page.tsx` | 관리자 페이지 진입 |
| `src/components/admin/AdminLogin.tsx` | 로그인 UI |
| `src/lib/adminNews.ts` | 관리자 뉴스 편집 |

**UI 표시만 추가 검토 시:**

- `src/app/reports/[date]/page.tsx`
- `src/components/NewsCard.tsx`

---

## 4. 선택 — 배포·프로젝트 메타

| 파일 | 언제 포함? |
|------|-----------|
| `package.json` | Next.js 의존성·스크립트 검토 시 |
| `DEPLOY.md` | Vercel·`ADMIN_PASSWORD` 배포 맥락 검토 시 |

---

## 5. 제외 (제시 금지)

| 항목 | 이유 |
|------|------|
| `.env.local` | `ADMIN_PASSWORD`, ntfy 토픽 등 실제 비밀 |
| `data/news.json` 전체 | 1900+ 줄 — `src/data/types.ts` 또는 앞 50~100줄만 |
| `raw_data/**` | 용량 큼, 크롤 결과물 |
| `logs/**` | 실행 로그 (실패 분석 시 해당 1개만) |
| `node_modules/`, `.next/`, `scripts/__pycache__/` | 빌드/캐시 |
| `data/news.backup.json` | 데이터 백업, 코드 검토 불필요 |

---

## 6. 검토 LLM 프롬프트 예시

파일 목록 **앞**에 아래 컨텍스트를 붙이면 검토 품질이 좋아집니다.

```text
프로젝트: bio-news-report (Next.js + Python RSS 크롤러)

반영된 작업:
- data/news.json 다일 리포트 + getReports
- Python 크롤러 (RSS → raw_data + news.json)
- 요약 한국어화: Google Translate (deep-translator), OpenAI 아님
- news.json / raw_data 90일 retention
- /admin 비밀번호 보호 (ADMIN_PASSWORD, 7일 세션 쿠키)
- GitHub Actions 일일 크롤 제거 → Windows 작업 스케줄러 09:30 KST
- run_daily_crawl.bat: 크롤 → git push(변경 시) → Vercel 자동 배포 → ntfy

검토 요청:
1) 보안(/admin, .env.local, git push 무인 실행)
2) 자동화 실패 시나리오(번역·push·알림)
3) news.json 무한 증가 대응(90일) 적절성
4) 문서와 코드 불일치 여부
```

---

## 7. 세트별 요약

| 목적 | 제시할 파일 |
|------|-------------|
| **전체 작업 제안 검토 (권장, ~22개)** | §1 + §2 + §3 |
| **크롤·스케줄·push·ntfy만** | §1 + `docs/windows_task_scheduler_setup.md` |
| **번역·데이터 정책만** | `collect_news.py`, `google_translate.py`, `translate_news_summaries.py`, `getReports.ts`, `types.ts` |
| **/admin 보안만** | §3 admin 관련 + `.env.local.example` |
| **운영·온보딩 검토** | §2 문서 3개 + `README.md` |

**빠른 아키텍처 검토 (약 10개):**  
`collect_news.py`, `google_translate.py`, `push_and_notify.py`, `notify_deploy.py`, `run_daily_crawl.bat`, `env_local.py`, `getReports.ts`, `types.ts`, `README.md`, `windows_task_scheduler_setup.md`

---

## 8. Windows에서 파일 묶기 (선택)

PowerShell에서 프로젝트 루트 기준:

```powershell
$files = Get-Content docs\llm_review_manifest.txt | Where-Object { $_ -and -not $_.StartsWith('#') }
$dest = "llm_review_bundle"
New-Item -ItemType Directory -Force -Path $dest | Out-Null
foreach ($f in $files) {
  if (Test-Path $f) {
    $target = Join-Path $dest $f
    New-Item -ItemType Directory -Force -Path (Split-Path $target) | Out-Null
    Copy-Item $f $target
  }
}
Write-Host "Copied to $dest/"
```

생성된 `llm_review_bundle/` 폴더를 압축해 다른 LLM에 업로드하면 됩니다.
