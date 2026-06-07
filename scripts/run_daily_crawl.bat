@echo off
setlocal EnableDelayedExpansion

REM ============================================================
REM Bio News Report - Daily crawl (Task Scheduler / manual)
REM 1. python scripts/collect_news.py
REM 2. git push (if news.json changed) + ntfy / Vercel notify
REM Logs: logs/daily_crawl_YYYY-MM-DD.log
REM Schedule: KST 09:30 daily (Windows Task Scheduler)
REM ============================================================

set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."
cd /d "%PROJECT_ROOT%" || (
  echo [ERROR] Cannot change to project root: %PROJECT_ROOT%
  exit /b 1
)

call :get_datetime
set "START_TIME=%DATETIME_ISO%"

set "LOG_DIR=%PROJECT_ROOT%\logs"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
set "LOG_FILE=!LOG_DIR!\daily_crawl_!LOG_DATE!.log"

set "PYTHON_CMD="
set "PYTHON_PATH="

where python >nul 2>&1
if !ERRORLEVEL! equ 0 (
  for /f "delims=" %%P in ('where python 2^>nul') do (
    set "PYTHON_PATH=%%P"
    set "PYTHON_CMD=python"
    goto :python_ready
  )
)

where py >nul 2>&1
if !ERRORLEVEL! equ 0 (
  for /f "delims=" %%P in ('where py 2^>nul') do set "PYTHON_PATH=%%P"
  set "PYTHON_CMD=py -3"
  goto :python_ready
)

set "END_TIME_FAIL=%START_TIME%"
call :write_log_header
>> "%LOG_FILE%" echo [PYTHON] NOT FOUND - install Python 3.10+ and add to PATH
>> "%LOG_FILE%" echo [RESULT] FAILED - Python not found
>> "%LOG_FILE%" echo [EXIT_CODE] 9009
>> "%LOG_FILE%" echo [END] %END_TIME_FAIL%
echo.
echo [FAILED] Python was not found. Install Python and run: pip install -r requirements.txt
echo Log file: %LOG_FILE%
exit /b 9009

:python_ready
call :write_log_header
>> "%LOG_FILE%" echo [PYTHON] %PYTHON_PATH%

>> "%LOG_FILE%" echo --------------------------------------------------
>> "%LOG_FILE%" echo [STEP] git pull
>> "%LOG_FILE%" echo [COMMAND] git pull --rebase --autostash
>> "%LOG_FILE%" echo --------------------------------------------------

echo.
echo Syncing latest config from GitHub (git pull)...
git pull --rebase --autostash >> "%LOG_FILE%" 2>&1
if !ERRORLEVEL! neq 0 (
  >> "%LOG_FILE%" echo [WARN] git pull failed - continuing with local files
  >> "%LOG_FILE%" echo [HINT] Resolve conflicts manually if crawl_config.json diverged
  echo [WARN] git pull failed - see log. Continuing with local files.
) else (
  echo git pull OK
)

>> "%LOG_FILE%" echo --------------------------------------------------
>> "%LOG_FILE%" echo [COMMAND] %PYTHON_CMD% scripts/collect_news.py
>> "%LOG_FILE%" echo --------------------------------------------------

echo.
echo Bio News Daily Crawl
echo Project: %CD%
echo Python:  %PYTHON_PATH%
echo Log:     %LOG_FILE%
echo.

%PYTHON_CMD% scripts/collect_news.py >> "%LOG_FILE%" 2>&1
set "EXIT_CODE=!ERRORLEVEL!"

if !EXIT_CODE! neq 0 goto :finish

>> "%LOG_FILE%" echo --------------------------------------------------
>> "%LOG_FILE%" echo [STEP] Git push and notify
>> "%LOG_FILE%" echo [COMMAND] %PYTHON_CMD% scripts/push_and_notify.py
>> "%LOG_FILE%" echo --------------------------------------------------

echo.
echo Running git push and ntfy notification...
%PYTHON_CMD% scripts/push_and_notify.py >> "%LOG_FILE%" 2>&1
set "EXIT_CODE=!ERRORLEVEL!"

:finish
call :get_datetime
set "END_TIME=%DATETIME_ISO%"

>> "%LOG_FILE%" echo --------------------------------------------------
if !EXIT_CODE! equ 0 (
  >> "%LOG_FILE%" echo [RESULT] SUCCESS
  echo [SUCCESS] All steps finished. See log: %LOG_FILE%
) else (
  >> "%LOG_FILE%" echo [RESULT] FAILED
  >> "%LOG_FILE%" echo [EXIT_CODE] !EXIT_CODE!
  echo [FAILED] Finished with exit code !EXIT_CODE!
  echo See log: %LOG_FILE%
)
>> "%LOG_FILE%" echo [END] %END_TIME%

set "RC=!EXIT_CODE!"
endlocal
exit /b %RC%

:write_log_header
>> "%LOG_FILE%" echo ==================================================
>> "%LOG_FILE%" echo [START] %START_TIME%
>> "%LOG_FILE%" echo [PROJECT_ROOT] %CD%
exit /b 0

:get_datetime
set "LOG_DATE=unknown-date"
set "DATETIME_ISO=unknown-time"
for /f "tokens=1* delims= " %%A in ('python "%SCRIPT_DIR%log_stamp.py" 2^>nul') do (
  set "LOG_DATE=%%A"
  set "DATETIME_ISO=%%A %%B"
)
if "!LOG_DATE!"=="unknown-date" (
  for /f "tokens=2 delims==" %%D in ('wmic os get localdatetime /value 2^>nul') do set "DT=%%D"
  if defined DT (
    set "DT=!DT:~0,14!"
    set "LOG_DATE=!DT:~0,4!-!DT:~4,2!-!DT:~6,2!"
    set "DATETIME_ISO=!DT:~0,4!-!DT:~4,2!-!DT:~6,2! !DT:~8,2!:!DT:~10,2!:!DT:~12,2!"
  )
)
exit /b 0

