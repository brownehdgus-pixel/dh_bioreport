# Windows 작업 스케줄러 — 매일 오전 09:30 (KST) 뉴스 수집·배포·알림

이 문서는 **비개발자**도 따라 할 수 있도록 작성했습니다.  
**GitHub Actions 일일 크롤은 사용하지 않습니다.** PC에서 **`scripts/run_daily_crawl.bat`** 을 매일 실행합니다.

---

## 자동 실행 흐름

```text
09:30 KST  작업 스케줄러
    │
    ├─► git pull --rebase --autostash  (Admin이 저장한 crawl_config 반영)
    │
    ├─► python scripts/collect_news.py     RSS 수집 → data/news.json, raw_data/
    │
    └─► python scripts/push_and_notify.py  (news.json 변경 시만)
            ├─► git commit & push  →  GitHub
            ├─► Vercel 자동 재배포
            └─► ntfy 푸시 (휴대폰)
```

| 하는 일 | 비고 |
|--------|------|
| RSS 뉴스 수집 | `raw_data/날짜/` 원본 저장 |
| `data/news.json` 갱신 | Google Translate로 요약 한국어 번역 |
| `data/crawl_config.json` | 크롤 소스·키워드·가중치 (Admin `/admin/crawl-settings`에서 편집 가능) |
| GitHub push | 변경 있을 때만 commit |
| Vercel 재배포 | GitHub 연동 시 자동 |
| ntfy 푸시 | `.env.local` 의 `NTFY_TOPIC` |
| `logs/daily_crawl_날짜.log` 기록 | 실패 시 여기서 확인 |

**90일 보관:** `news.json`·`raw_data` 는 최근 90일만 유지합니다.

---

## A. 사전 준비 (한 번만)

### 1) Python 설치

1. https://www.python.org/downloads/ 에서 **Python 3.10 이상** 설치
2. 설치 화면에서 **「Add python.exe to PATH」** 반드시 체크
3. **새** 명령 프롬프트에서 확인:

```text
python --version
```

### 2) Python 패키지 설치

프로젝트 폴더(예: `C:\projects\bio-news-report`)에서:

```text
pip install -r requirements.txt
```

### 3) `.env.local` 설정 (크롤·번역·푸시)

1. **`.env.local.example`** 을 복사해 **`.env.local`** 로 저장
2. 아래 값을 채웁니다:

| 변수 | 용도 |
|------|------|
| `NTFY_TOPIC` | ntfy 앱에서 구독한 **비공개** 토픽 이름 |
| `VERCEL_PRODUCTION_URL` | 알림 링크 (예: `https://본인프로젝트.vercel.app`) |
| `VERCEL_TOKEN`, `VERCEL_PROJECT_ID` | (선택) 배포 **READY** 후 알림 |

> 번역은 **Google Translate** (무료, API 키 불필요). `pip install -r requirements.txt` 로 `deep-translator` 설치.

**ntfy 앱:** Play Store / App Store에서 **ntfy** 설치 → **+ Subscribe to topic** → `.env.local` 과 **같은 토픽** 입력.

> `.env.local` 은 Git에 올라가지 않습니다. PC에만 둡니다.

### 4) GitHub push 권한 (무인 실행 필수)

작업 스케줄러는 **로그인 창 없이** `git push` 를 실행해야 합니다.

**권장 방법 (택 1):**

1. **GitHub Desktop** — 저장소를 열고 한 번 **Fetch/Push** 성공시키기 (자격 증명 저장)
2. **Git Credential Manager** — VS Code / Git for Windows로 push 한 번 성공
3. **Personal Access Token** — HTTPS remote + 토큰 저장

확인: 명령 프롬프트에서 프로젝트 폴더로 이동 후:

```text
git push
```

오류 없이 push 되면 스케줄러에서도 동작할 가능성이 높습니다.

---

## B. 사전 테스트 (작업 스케줄러 등록 **전** 필수)

### 1) 테스트 배치 파일 더블클릭

1. **`scripts\test_daily_crawl.bat`** 더블클릭
2. **`SUCCESS`** 가 보이면 성공
3. 로그·GitHub·ntfy까지 확인:

| 확인 | 기대 결과 |
|------|-----------|
| `logs\daily_crawl_오늘.log` | `[RESULT] SUCCESS`, push/ntfy 단계 로그 |
| `data\news.json` | 수정 시간 갱신 |
| GitHub 저장소 | `chore: update daily bio news report` commit (변경 시) |
| Vercel | 새 배포 (GitHub 연동 시) |
| ntfy 앱 | 「바이오 뉴스…」 푸시 |

---

## C. 작업 스케줄러 등록

### 1) 작업 스케줄러 열기

Windows 키 → **「작업 스케줄러」** → **「작업 만들기…」**  
(「기본 작업 만들기」가 아님)

### 2) 일반 탭

| 항목 | 설정값 |
|------|--------|
| 이름 | `Bio News Daily Crawl` |
| 설명 | `매일 09:30 KST 바이오 뉴스 크롤·push·알림` |
| 보안 옵션 | **사용자가 로그온되어 있지 않아도 실행** |
| | **가장 높은 수준의 권한으로 실행** |

### 3) 트리거 탭 → 새로 만들기

| 항목 | 값 |
|------|-----|
| 작업 시작 | **일정에 따라** |
| 설정 | **매일** |
| 시작 | **09:30:00** |
| 사용 | **체크** |

> PC 시간대가 **(UTC+09:00) 서울** 이면 09:30 = KST 09:30 입니다.

### 4) 동작 탭 → 새로 만들기

| 항목 | 값 |
|------|-----|
| 동작 | **프로그램 시작** |
| 프로그램/스크립트 | `C:\projects\bio-news-report\scripts\run_daily_crawl.bat` |
| 시작 위치 | `C:\projects\bio-news-report` |

경로는 본인 PC에 맞게 수정하세요.

### 5) 조건 탭

| 옵션 | 권장 |
|------|------|
| **작업을 실행하기 위해 컴퓨터를 절전 모드에서 해제** | **체크** |
| **컴퓨터가 AC 전원일 때만 작업 시작** | 노트북이면 **체크** 권장 |

### 6) 설정 탭

| 옵션 | 권장 |
|------|------|
| **예약된 시작을 놓친 경우 가능한 한 빨리 작업 실행** | **체크** |
| **작업이 실패하면 다음 시간 간격으로 다시 시도** | **체크** — 15분, 1시간 |
| **작업이 실행 중일 때 규칙 적용** | **새 인스턴스를 시작하지 않음** |

### 7) 전원 (노트북)

09:30에 **절전/꺼짐** 이면 실행되지 않습니다.  
09:30 전후 PC가 켜져 있거나, 절전 해제 타이머를 켜 두세요.

---

## D. 등록 후 수동 테스트

1. **작업 스케줄러 라이브러리** → **Bio News Daily Crawl** → **우클릭 → 실행**
2. 2~5분 후 `logs\daily_crawl_오늘.log` 에 `[RESULT] SUCCESS` 확인

---

## E. 실패 시 확인

| 증상 | 확인 |
|------|------|
| Python 없음 | 로그 `[PYTHON] NOT FOUND`, `[EXIT_CODE] 9009` — `.env.local`에 `PYTHON_EXECUTABLE` 전체 경로 |
| `ModuleNotFoundError` | `pip install -r requirements.txt` |
| 번역 실패 | 인터넷 연결, `pip install -r requirements.txt` (`deep-translator`) |
| `Git push failed` | GitHub 로그인·토큰, `git push` 수동 테스트 |
| 푸시 알림 없음 | `NTFY_TOPIC`, ntfy 앱 구독, 로그의 `ntfy:` 줄 |
| **크롤 실패 알림** | 로그 `[FAIL_STEP]`, ntfy 「데일리 크롤 실패」 (push 전 단계 실패 시) |
| 09:30에 안 돌아감 | PC 절전, 작업 비밀번호 만료, 트리거 시간, 작업 스케줄러 **기록** 탭 |

### 로그 진단 필드 (2026-06 이후 bat)

`logs\daily_crawl_날짜.log` 상단에 다음이 기록됩니다:

| 줄 | 의미 |
|----|------|
| `[DIAG] USERNAME`, `SESSIONNAME` | 어떤 계정·세션에서 실행됐는지 |
| `[PYTHON] C:\...\python.exe` | 실제 사용된 Python **절대 경로** |
| `[GIT]` | git PATH 여부 |
| `[ENV] .env.local present` | ntfy용 env 파일 존재 |
| `[FAIL_STEP]` | `python` / `collect_news` / `push_and_notify` 중 실패 단계 |

**작업 스케줄러 기록 탭:** 6/8 09:30에 **작업 시작됨(200)** 이 없으면 PC 절전·트리거 OFF 가능성이 큽니다.

**수동 복구:** `scripts\test_daily_crawl.bat` 실행 → 성공 후 다음날 09:30 재확인.

---

## F. 경로 요약

| 용도 | 예시 |
|------|------|
| 프로젝트 루트 | `C:\projects\bio-news-report` |
| 자동 실행 | `scripts\run_daily_crawl.bat` |
| 수동 테스트 | `scripts\test_daily_crawl.bat` |
| 환경 변수 | `.env.local` (Git 제외) |
| 로그 | `logs\daily_crawl_YYYY-MM-DD.log` |

---

## G. 자주 묻는 질문

**Q. GitHub Actions는요?**  
→ 일일 크롤용 워크플로는 **제거**되었습니다. PC 작업 스케줄러만 사용합니다.

**Q. news.json이 안 바뀌면 push도 안 하나요?**  
→ 맞습니다. 변경 없으면 commit/push·알림을 건너뜁니다.

**Q. Vercel은 어떻게 반영되나요?**  
→ GitHub에 push 되면 Vercel이 **자동 재배포**합니다 (저장소 연동 필요).

---

*문서 버전: Windows 09:30 KST + git push + ntfy*
