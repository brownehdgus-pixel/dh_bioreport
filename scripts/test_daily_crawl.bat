@echo off
REM Manual test - double-click to run daily crawl and review output before Task Scheduler setup.

echo ============================================================
echo  Bio News - Daily Crawl TEST (manual)
echo  This runs the same script as the scheduled task.
echo ============================================================
echo.

call "%~dp0run_daily_crawl.bat"
set "TEST_EXIT=%ERRORLEVEL%"

echo.
echo ============================================================
if %TEST_EXIT% equ 0 (
  echo  Test finished: SUCCESS
  echo  Check folder: logs\
  echo  Check files:  data\news.json , raw_data\
  echo  If news changed: GitHub commit, Vercel deploy, ntfy push
) else (
  echo  Test finished: FAILED (code %TEST_EXIT%)
  echo  Open the latest file in logs\ folder for details.
)
echo ============================================================
echo.
pause

exit /b %TEST_EXIT%
