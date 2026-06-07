# Bio Industry Daily Memo

모바일 우선 개인용 바이오 산업 뉴스 리포트 웹앱입니다. (뉴스 데이터: `data/news.json` · DB 없음)

---

## 실행 방법 (처음 한 번만 설치)

### 1단계: Node.js 설치

아직 Node.js가 없다면 아래 사이트에서 **LTS** 버전을 설치하세요.

- https://nodejs.org/ko

설치 후 **컴퓨터를 한 번 재시작**하거나, **새 터미널**을 열어주세요.

설치 확인 (터미널 또는 PowerShell):

```bash
node -v
npm -v
```

버전 숫자가 나오면 성공입니다.

### 2단계: 패키지 설치

터미널에서 이 폴더로 이동한 뒤:

```bash
cd bio-news-report
npm install
```

처음에는 1~3분 정도 걸릴 수 있습니다.

### 3단계: 개발 서버 실행

```bash
npm run dev
```

터미널에 `Local: http://localhost:3000` 이 보이면 브라우저에서 해당 주소를 엽니다.

**휴대폰에서 보려면:** PC와 같은 Wi‑Fi에 연결한 뒤, PC의 IP 주소로 접속합니다.  
예: `http://192.168.0.10:3000` (IP는 `ipconfig` 명령으로 확인)

### 종료

터미널에서 `Ctrl + C` 를 누르면 서버가 종료됩니다.

---

## 폴더 구조

| 경로 | 설명 |
|------|------|
| `data/news.json` | **모든 날짜의 뉴스 리포트** (여기서 내용 수정) |
| `src/lib/getReports.ts` | JSON 파일을 읽어 화면에 넘기는 로직 (나중에 Supabase로 교체) |
| `src/components/` | 화면 UI (디자인만 담당, 데이터는 직접 읽지 않음) |
| `src/app/reports/` | 리포트 목록·날짜별 상세 페이지 |

---

## 뉴스 데이터 수정하기 (`data/news.json`)

코드가 아니라 **`data/news.json`** 파일 하나에 여러 날짜 리포트가 들어 있습니다.

### 파일 구조 (간단히)

```text
reports → [ 날짜별 리포트, 날짜별 리포트, ... ]
```

**각 리포트(하루치)** 에는 다음이 있습니다.

| 필드 | 의미 |
|------|------|
| `reportDate` | 날짜 (예: `2026-06-04`) |
| `title` | 상단 제목 |
| `summaryLines` | 핵심 요약 줄 (배열) |
| `sections` | 탭에 쓸 섹션 목록 |
| `items` | 그날의 뉴스 카드 목록 |

**각 뉴스 카드(`items` 안 한 건)** 에는 제목, 출처, 요약, 의미, 키워드, URL, 중요도·국내 연관 점수 등이 들어갑니다.

### 수정 후 반영

1. `data/news.json` 을 저장합니다.
2. 개발 중이면 브라우저 **새로고침** (필요 시 `npm run dev` 재시작).
3. Vercel에 배포한 경우에는 Git에 올린 뒤 **다시 배포**해야 반영됩니다.

### 관리자 화면으로 추가하기

`/admin` 에서 비밀번호로 로그인 → 뉴스 입력 → **JSON 복사** → `data/news.json` 의 해당 날짜 `items` 배열에 붙여넣기.

---

## 뉴스 자동 수집 (Python 크롤링 MVP)

RSS에서 기사를 모아 **`data/news.json`** 을 자동으로 갱신합니다. (Supabase·LLM은 이후 단계)

### 1단계: Python 설치

- https://www.python.org/downloads/ 에서 **Python 3.10 이상** 설치
- 설치 시 **「Add Python to PATH」** 체크

확인:

```bash
python --version
```

### 2단계: 패키지 설치 (프로젝트 폴더에서)

```bash
cd bio-news-report
pip install -r requirements.txt
```

### 3단계: 수집 실행

```bash
python scripts/collect_news.py
```

### 생성되는 파일

| 파일 | 설명 |
|------|------|
| `raw_data/날짜/raw_items.json` | RSS에서 받은 **원본** |
| `raw_data/날짜/deduplicated_items.json` | URL 기준 **중복 제거** 후 |
| `data/news.backup.json` | 갱신 전 `news.json` **백업** |
| `data/news.json` | 웹앱이 읽는 **최종** 데이터 |

### 4단계: 웹에서 확인

```bash
npm run dev
```

브라우저에서 `/reports` → 오늘 날짜 리포트 선택.

**수집 소스:** Fierce Biotech·Pharma, BioPharma Dive, Business Wire RSS, Google News 키워드 검색.

**참고:** `importanceScore`·`koreaRelevanceScore`는 JSON에만 저장되고, 화면 카드에는 표시하지 않습니다.

**영문 요약 한글화:** 크롤 시 **Google Translate**로 `summary`를 한국어로 번역합니다 (API 키 불필요).  
기존 `news.json`만 고치려면: `python scripts/translate_news_summaries.py`

**용량 관리:** `news.json`·`raw_data`는 **최근 90일**만 유지합니다.

### 크롤 선정 기준 (`data/crawl_config.json`)

RSS/Google 쿼리, 키워드 분류, 가중치, `excludeKeywords`, 리포트 한도(14일·40건 등)는 **`data/crawl_config.json`** 에 정의됩니다.

| 경로 | 용도 |
|------|------|
| `data/crawl_config.json` | 크롤 소스·분류·점수 설정 |
| `/admin/crawl-settings` | Admin JSON 편집 → GitHub 저장 |
| `scripts/crawl_config.py` | Python 로드·검증 |

Vercel env: `GITHUB_TOKEN`, `GITHUB_REPO` (Admin 저장용). `crawl_config.json`만 변경된 commit은 Vercel build skip (`scripts/vercel-should-build.sh`).

### Windows 작업 스케줄러 매일 자동 수집 (권장 · 오전 09:30 KST)

내 PC에서 매일 크롤러를 실행하고, `data/news.json`이 바뀌면 **자동 commit/push** → **Vercel 자동 재배포** → **ntfy 푸시 알림**.

| 파일 | 용도 |
|------|------|
| `scripts/run_daily_crawl.bat` | git pull → 크롤 → push → 알림 (작업 스케줄러) |
| `scripts/push_and_notify.py` | Git push + ntfy |
| `scripts/test_daily_crawl.bat` | **더블클릭** 수동 테스트 |
| `logs/daily_crawl_YYYY-MM-DD.log` | 실행 로그 |
| `docs/windows_task_scheduler_setup.md` | 등록 방법 (비개발자용) |

**`.env.local` (PC 전용):** `NTFY_TOPIC` · `VERCEL_PRODUCTION_URL` — `.env.local.example` 참고.

**테스트 순서 (요약):**

1. `.env.local` 설정 + `pip install -r requirements.txt`  
2. `git push` 가 수동으로 되는지 확인 (GitHub 자격 증명)  
3. `scripts\test_daily_crawl.bat` 더블클릭 → commit → Vercel → ntfy 확인  
4. `docs/windows_task_scheduler_setup.md` 따라 **09:30** 트리거 등록  

**Vercel:** push 시 **자동 재배포**. GitHub Actions 일일 크롤은 **사용하지 않습니다** (`docs/github_actions_setup.md` 참고).

---

## 관리자 페이지 (`/admin`) 비밀번호

뉴스 입력 화면은 **관리자 비밀번호**로만 들어갈 수 있습니다. (나중에 Supabase 로그인으로 바꿀 예정이며, 지금은 간단한 비밀번호 방식입니다.)

### 로컬에서 비밀번호 설정

1. 프로젝트 폴더에 있는 **`.env.local.example`** 파일을 복사해 **`.env.local`** 로 저장합니다.
2. `.env.local` 안의 `ADMIN_PASSWORD=` 뒤에 **원하는 비밀번호**를 적습니다.
3. 개발 서버를 **끄고** (`Ctrl + C`) 다시 **`npm run dev`** 로 실행합니다.
4. 브라우저에서 `http://localhost:3000/admin` (또는 터미널에 나온 포트)을 엽니다.

`.env.local` 은 Git에 올라가지 않으므로 비밀번호가 공개되지 않습니다.

### Vercel(배포 사이트)에서 비밀번호 설정

1. [Vercel](https://vercel.com) → 해당 프로젝트 선택
2. **Settings** → **Environment Variables**
3. **Key:** `ADMIN_PASSWORD` / **Value:** 관리자 비밀번호 입력
4. **Production** (필요하면 Preview·Development도) 체크 후 **Save**
5. **Deployments** → 최신 배포 **⋯** → **Redeploy** (환경 변수는 재배포 후 적용됩니다)

자세한 배포 절차는 `DEPLOY.md` 를 참고하세요.

### 동작 요약

| 상황 | 화면 |
|------|------|
| `/admin` 첫 방문 | 비밀번호 입력 화면 |
| 비밀번호 맞음 | 뉴스 입력 화면 (7일 동안 쿠키로 유지, 새로고침해도 재입력 없음) |
| 비밀번호 틀림 | 「비밀번호가 올바르지 않습니다」 |
| 「로그아웃」 클릭 | 다시 비밀번호 입력 화면 |

---

## 기술 스택

- Next.js 15 (App Router)
- React 19
- Tailwind CSS 3
- TypeScript
