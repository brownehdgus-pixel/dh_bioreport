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
