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
set "FAIL_STEP=unknown"
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

call :find_python
if !ERRORLEVEL! neq 0 goto :python_missing

:python_ready
call :write_log_header
call :log_diagnostics

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

set "FAIL_STEP=collect_news"
>> "%LOG_FILE%" echo --------------------------------------------------
>> "%LOG_FILE%" echo [STEP] collect_news
>> "%LOG_FILE%" echo [COMMAND] !PYTHON_CMD! scripts/collect_news.py
>> "%LOG_FILE%" echo --------------------------------------------------

echo.
echo Bio News Daily Crawl
echo Project: %CD%
echo Python:  !PYTHON_PATH!
echo Log:     !LOG_FILE!
echo.

!PYTHON_CMD! scripts/collect_news.py >> "%LOG_FILE%" 2>&1
set "EXIT_CODE=!ERRORLEVEL!"

if !EXIT_CODE! neq 0 goto :finish

set "FAIL_STEP=push_and_notify"
>> "%LOG_FILE%" echo --------------------------------------------------
>> "%LOG_FILE%" echo [STEP] Git push and notify
>> "%LOG_FILE%" echo [COMMAND] !PYTHON_CMD! scripts/push_and_notify.py
>> "%LOG_FILE%" echo --------------------------------------------------

echo.
echo Running git push and ntfy notification...
!PYTHON_CMD! scripts/push_and_notify.py >> "%LOG_FILE%" 2>&1
set "EXIT_CODE=!ERRORLEVEL!"

goto :finish

:python_missing
set "EXIT_CODE=9009"
set "FAIL_STEP=python"
set "END_TIME_FAIL=%START_TIME%"
call :write_log_header
>> "%LOG_FILE%" echo [PYTHON] NOT FOUND
>> "%LOG_FILE%" echo [HINT] Set PYTHON_EXECUTABLE in .env.local to full path to python.exe
>> "%LOG_FILE%" echo [HINT] Or install Python 3.10+ with Add to PATH
call :log_diagnostics
call :notify_failure
>> "%LOG_FILE%" echo [RESULT] FAILED - Python not found
>> "%LOG_FILE%" echo [EXIT_CODE] 9009
>> "%LOG_FILE%" echo [END] %END_TIME_FAIL%
echo.
echo [FAILED] Python was not found. Set PYTHON_EXECUTABLE in .env.local
echo Log file: !LOG_FILE!
exit /b 9009

:finish
call :get_datetime
set "END_TIME=%DATETIME_ISO%"

>> "%LOG_FILE%" echo --------------------------------------------------
if !EXIT_CODE! equ 0 (
  >> "%LOG_FILE%" echo [RESULT] SUCCESS
  echo [SUCCESS] All steps finished. See log: !LOG_FILE!
) else (
  >> "%LOG_FILE%" echo [RESULT] FAILED
  >> "%LOG_FILE%" echo [EXIT_CODE] !EXIT_CODE!
  >> "%LOG_FILE%" echo [FAIL_STEP] !FAIL_STEP!
  echo [FAILED] Finished with exit code !EXIT_CODE! ^(!FAIL_STEP!^)
  echo See log: !LOG_FILE!
  call :notify_failure
)
>> "%LOG_FILE%" echo [END] %END_TIME%

set "RC=!EXIT_CODE!"
endlocal
exit /b %RC%

:find_python
set "PYTHON_CMD="
set "PYTHON_PATH="

REM 1) py launcher + resolve_python.py (reads .env.local PYTHON_EXECUTABLE)
where py >nul 2>&1
if !ERRORLEVEL! equ 0 (
  for /f "usebackq delims=" %%P in (`py -3 "%SCRIPT_DIR%resolve_python.py" 2^>nul`) do (
    set "PYTHON_PATH=%%P"
    set "PYTHON_CMD=%%P"
    exit /b 0
  )
)

REM 2) python on PATH + resolve_python.py
where python >nul 2>&1
if !ERRORLEVEL! equ 0 (
  for /f "usebackq delims=" %%P in (`python "%SCRIPT_DIR%resolve_python.py" 2^>nul`) do (
    set "PYTHON_PATH=%%P"
    set "PYTHON_CMD=%%P"
    exit /b 0
  )
)

REM 3) Common Windows install paths (Task Scheduler often has empty PATH)
if defined LOCALAPPDATA (
  for %%V in (314 313 312 311 310) do (
    if exist "!LOCALAPPDATA!\Programs\Python\Python%%V\python.exe" (
      set "PYTHON_PATH=!LOCALAPPDATA!\Programs\Python\Python%%V\python.exe"
      set "PYTHON_CMD=!LOCALAPPDATA!\Programs\Python\Python%%V\python.exe"
      exit /b 0
    )
  )
)

REM 4) where python / py -3 as last resort
where python >nul 2>&1
if !ERRORLEVEL! equ 0 (
  for /f "delims=" %%P in ('where python 2^>nul') do (
    set "PYTHON_PATH=%%P"
    set "PYTHON_CMD=%%P"
    exit /b 0
  )
)

where py >nul 2>&1
if !ERRORLEVEL! equ 0 (
  for /f "usebackq delims=" %%P in (`py -3 -c "import sys; print(sys.executable)" 2^>nul`) do (
    set "PYTHON_PATH=%%P"
    set "PYTHON_CMD=%%P"
    exit /b 0
  )
)

exit /b 1

:log_diagnostics
>> "%LOG_FILE%" echo [DIAG] USERNAME=%USERNAME% COMPUTERNAME=%COMPUTERNAME%
>> "%LOG_FILE%" echo [DIAG] USERDOMAIN=%USERDOMAIN% SESSIONNAME=%SESSIONNAME%
>> "%LOG_FILE%" echo [DIAG] SCHEDULED_TASK=%SCHEDULED_TASK_NAME%
if defined PYTHON_CMD (
  >> "%LOG_FILE%" echo [PYTHON] !PYTHON_PATH!
  !PYTHON_CMD! -V >> "%LOG_FILE%" 2>&1
  !PYTHON_CMD! -c "import sys; print('[PYTHON] executable=', sys.executable)" >> "%LOG_FILE%" 2>&1
)
where git >nul 2>&1
if !ERRORLEVEL! equ 0 (
  for /f "delims=" %%G in ('where git 2^>nul') do (
    >> "%LOG_FILE%" echo [GIT] %%G
    goto :diag_git_done
  )
) else (
  >> "%LOG_FILE%" echo [GIT] NOT FOUND in PATH
)
:diag_git_done
if exist "%PROJECT_ROOT%\.env.local" (
  >> "%LOG_FILE%" echo [ENV] .env.local present
) else (
  >> "%LOG_FILE%" echo [WARN] .env.local missing - ntfy will not work
)
exit /b 0

:notify_failure
if not defined PYTHON_CMD (
  where py >nul 2>&1
  if !ERRORLEVEL! equ 0 (
    py -3 "%SCRIPT_DIR%notify_task_failure.py" "!FAIL_STEP!" "!EXIT_CODE!" "!LOG_FILE!" >> "%LOG_FILE%" 2>&1
  )
  exit /b 0
)
!PYTHON_CMD! "%SCRIPT_DIR%notify_task_failure.py" "!FAIL_STEP!" "!EXIT_CODE!" "!LOG_FILE!" >> "%LOG_FILE%" 2>&1
exit /b 0

:write_log_header
>> "%LOG_FILE%" echo ==================================================
>> "%LOG_FILE%" echo [START] %START_TIME%
>> "%LOG_FILE%" echo [PROJECT_ROOT] %CD%
exit /b 0

:get_datetime
set "LOG_DATE=unknown-date"
set "DATETIME_ISO=unknown-time"
if defined PYTHON_CMD (
  for /f "tokens=1* delims= " %%A in ('!PYTHON_CMD! "%SCRIPT_DIR%log_stamp.py" 2^>nul') do (
    set "LOG_DATE=%%A"
    set "DATETIME_ISO=%%A %%B"
  )
)
if "!LOG_DATE!"=="unknown-date" (
  where py >nul 2>&1
  if !ERRORLEVEL! equ 0 (
    for /f "tokens=1* delims= " %%A in ('py -3 "%SCRIPT_DIR%log_stamp.py" 2^>nul') do (
      set "LOG_DATE=%%A"
      set "DATETIME_ISO=%%A %%B"
    )
  )
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
