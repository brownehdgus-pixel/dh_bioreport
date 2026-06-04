# GitHub Actions — 매일 오전 09:30 뉴스 자동 수집

이 문서는 **비개발자**도 따라 할 수 있도록 작성했습니다.  
Windows 작업 스케줄러 대신 **GitHub Actions**가 매일 크롤러를 실행하고, 변경이 있으면 GitHub에 올린 뒤 **Vercel**이 웹사이트를 자동으로 다시 배포합니다.

---

## GitHub Actions란?

**GitHub Actions**는 GitHub 저장소에 연결된 **클라우드 컴퓨터**에서, 정해진 시간이나 버튼 클릭에 맞춰 스크립트를 실행하는 기능입니다.

이 프로젝트에서는:

1. 매일 **오전 09:30 (한국 시간)** 에 뉴스 수집 프로그램 실행  
2. `data/news.json`, `raw_data/` 등 갱신  
3. 내용이 바뀌었으면 GitHub에 **자동 저장(commit·push)**  
4. Vercel이 push를 감지해 **웹사이트 자동 재배포**

```text
[09:30 KST] GitHub Actions 실행
    → python scripts/collect_news.py
    → data/news.json · raw_data/ 저장
    → (변경 있으면) GitHub push
    → Vercel 자동 재배포
    → 인터넷 /reports 에 새 뉴스 반영
```

**이번 단계에서 하지 않는 것:** Supabase DB 저장, LLM 요약, Telegram 알림, Windows 작업 스케줄러.

---

## 사전 준비 (한 번만)

| 항목 | 확인 방법 |
|------|-----------|
| 코드가 GitHub에 있음 | 브라우저에서 github.com → 본인 저장소 → `README.md` 등 파일 보임 |
| 기본 브랜치 | 보통 **`main`** (Vercel Production과 같아야 함) |
| Vercel 연결 | Vercel 대시보드 → 프로젝트 → Git 연결된 저장소 표시 |
| Actions 활성화 | 저장소 → **Settings** → **Actions** → General에서 워크플로 실행 허용 |
| 관리자 비밀번호 | Vercel **Environment Variables**에 `ADMIN_PASSWORD` 등록 (`/admin`용) |

로컬 PC가 꺼져 있어도 GitHub Actions는 **GitHub 서버**에서 돌아갑니다.

---

## 매일 09:30 KST 실행 구조

| 구분 | 값 |
|------|-----|
| 한국 시간 | **매일 09:30** |
| GitHub cron (UTC) | **00:30** (`30 0 * * *`) |
| 워크플로 파일 | `.github/workflows/daily-crawl.yml` |
| 실행 환경 | `ubuntu-latest` |
| 크롤러 명령 | `python scripts/collect_news.py` |

한국은 서머타임이 없어서 **09:30 KST = 00:30 UTC** 로 고정합니다.

---

## Actions 탭에서 수동 실행하기

스케줄을 기다리지 않고 **지금 바로** 테스트할 때:

1. GitHub 저장소 페이지 접속  
2. 상단 **Actions** 탭 클릭  
3. 왼쪽 목록에서 **Daily Bio News Crawl** 선택  
4. 오른쪽 **Run workflow** 버튼 클릭  
5. 브랜치 **`main`** 확인 → **Run workflow** 다시 클릭  
6. 목록에 새 **Run**이 생기면 클릭해 진행 상황 확인  

1~3분 정도 걸릴 수 있습니다.

---

## 실행 성공 / 실패 확인

### 성공

- Run 목록에 **초록색 체크** 표시  
- 각 단계(Step)도 초록색  
- **Run news crawler** 단계 로그에 RSS 수집 건수, `Done` 요약이 보임  
- **Commit and push** 단계에서  
  - `data/news.json unchanged — skipping commit` → 데이터 변경 없음 (정상 종료)  
  - 또는 commit 후 push 완료  

### 실패

- Run에 **빨간색 X**  
- 실패한 Step을 클릭해 **빨간 로그** 확인  

**참고:** 특정 RSS 소스만 `FAILED` 로 나와도, 크롤러는 **전체를 중단하지 않을 수 있습니다**. Run 전체가 빨간색일 때만 “실패”로 보면 됩니다.

---

## GitHub 자동 commit → Vercel 자동 재배포

1. Actions가 `data/news.json`을 **실제로 변경**했을 때만 commit  
   - 메시지: `chore: update daily bio news report`  
   - 작성자: `github-actions[bot]`  
2. GitHub `main` 브랜치에 push  
3. Vercel이 push를 감지해 **새 Deployment** 시작  
4. 배포가 끝나면 Production URL의 **`/reports`** 에 반영  

### Vercel에서 확인

1. [vercel.com](https://vercel.com) → 프로젝트  
2. **Deployments** 탭  
3. 최신 항목이 **Building** → **Ready** 인지 확인  
4. 사이트 주소 → `/reports` → 오늘 날짜 리포트 확인  

---

## 실패 시 로그 확인 방법

1. **Actions** → 실패한 **Run** 클릭  
2. 실패한 **Step** 펼치기 (보통 **Run news crawler** 또는 **Commit and push**)  
3. 로그에서 `Error`, `FAILED`, `ModuleNotFoundError` 등 검색  

| 증상 | 대처 |
|------|------|
| `ModuleNotFoundError: feedparser` | `requirements.txt` 누락·손상 — 저장소에 파일 있는지 확인 |
| `python: command not found` | workflow 파일 손상 가능 — `.github/workflows/daily-crawl.yml` 복구 |
| push 권한 오류 | workflow에 `permissions: contents: write` 있는지 확인 |
| RSS 일부 FAILED | 인터넷·해당 사이트 일시 장애 — 다음 날 재시도 |

**로컬 `logs/` 폴더:** GitHub Actions는 여기에 파일을 남기지 않습니다. 로그는 **Actions Run 화면**이 전부입니다.

---

## Private 저장소일 때 (Actions 사용량)

- **Private** 저장소는 GitHub Actions **무료 사용 시간(분)** 이 제한됩니다.  
- 이 크롤러는 Run당 대략 **1~3분** 수준입니다.  
- 매일 1회면 보통 무료 한도 안에서 동작합니다.  
- 한도 초과 시 billing 설정 또는 Public 전환 검토가 필요할 수 있습니다.  
- 자세한 한도: GitHub → **Settings** → **Billing** 또는 [GitHub Actions 문서](https://docs.github.com/en/actions/learn-github-actions/usage-limits-billing-and-administration)

---

## raw_data를 GitHub에 올릴 때 (용량)

- 크롤러는 `raw_data/날짜/` 아래에 **원본 JSON**을 저장합니다.  
- Actions가 commit할 때 `raw_data/`도 함께 올라갑니다.  
- **며칠·몇 달이 지나면 저장소 용량이 커질 수 있습니다.**  

나중에 **Supabase** 등 DB를 쓰면:

- 원본·리포트를 DB에만 저장  
- GitHub에는 코드만 두고 **자동 commit을 끄는** 방식으로 바꿀 수 있습니다.  
- 그때는 웹앱이 DB에서 읽도록 `getReports.ts`만 교체하면 됩니다.

---

## Windows 작업 스케줄러와의 관계

| 방식 | 용도 |
|------|------|
| **GitHub Actions (권장)** | 매일 09:30 · GitHub push · Vercel 자동 배포 |
| `scripts/run_daily_crawl.bat` | **내 PC에서만** 로컬 `news.json` 갱신 (선택) |

이번 자동화 단계에서는 **작업 스케줄러 등록은 필요 없습니다.**  
로컬 테스트는 `docs/windows_task_scheduler_setup.md` 또는 `scripts/test_daily_crawl.bat`를 참고하세요.

---

## 사용자 테스트 체크리스트

1. [ ] `.github/workflows/daily-crawl.yml` 이 포함된 상태로 **GitHub `main`에 push**  
2. [ ] **Actions** → **Daily Bio News Crawl** → **Run workflow** (수동 1회)  
3. [ ] Run **초록색** + crawler 로그 정상  
4. [ ] (데이터 변경 시) GitHub **Commits**에 `chore: update daily bio news report`  
5. [ ] Vercel **Deployments** 새 배포 **Ready**  
6. [ ] Production URL **`/reports`** 에 오늘 리포트·한글 요약 확인  

---

## 관련 파일

| 파일 | 설명 |
|------|------|
| `.github/workflows/daily-crawl.yml` | Actions 워크플로 정의 |
| `scripts/collect_news.py` | 기존 크롤러 (수정 없음) |
| `requirements.txt` | Python 패키지 목록 |
| `data/news.json` | 웹앱이 읽는 리포트 데이터 |
| `DEPLOY.md` | Vercel·GitHub 최초 연결 |

---

*문서 버전: GitHub Actions 일일 크롤 기준*
