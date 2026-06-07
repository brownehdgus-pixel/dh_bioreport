# GitHub Actions 일일 크롤 — 사용 중단

**데일리 크롤은 Windows 작업 스케줄러로 실행합니다.**

- 실행 시각: **매일 오전 09:30 (KST)**
- 설정 가이드: **[windows_task_scheduler_setup.md](windows_task_scheduler_setup.md)**

`.github/workflows/daily-crawl.yml` 은 제거되었습니다.  
크롤 → GitHub push → Vercel 재배포 → **ntfy 푸시** 는 PC의 `scripts/run_daily_crawl.bat` 이 처리합니다.
