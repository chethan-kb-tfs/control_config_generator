@echo off
REM ============================================================
REM run.bat
REM Everyday launcher. Always targets the fixed install location
REM created by install.bat (%USERPROFILE%\control_config_generator),
REM regardless of where this script itself is run from.
REM
REM   1. Checks the "dev" branch on GitHub for a newer version.
REM      - If one is found, pulls it, reinstalls dependencies only
REM        if requirements.txt changed, and reports old -> new version.
REM      - If already up to date, or GitHub can't be reached, just
REM        continues with what's on disk (never blocks on network).
REM   2. Uses the existing virtual environment if present, or
REM      creates it (and installs dependencies) if missing.
REM   3. Starts app.py in its own window.
REM   4. Opens the app in Chrome (falls back to the default
REM      browser if Chrome cannot be found).
REM ============================================================
setlocal enabledelayedexpansion

set INSTALL_DIR=%USERPROFILE%\control_config_generator
set VENV_DIR=%INSTALL_DIR%\venv
set APP_URL=http://127.0.0.1:5000
set APP_TITLE=Databricks SQL Insert Generator
set BRANCH=dev
set NEEDS_INSTALL=0

echo ==============================================
echo  %APP_TITLE%
echo ==============================================
echo.

if not exist "%INSTALL_DIR%\app.py" (
    echo ERROR: App not found at "%INSTALL_DIR%".
    echo Run install.bat first.
    pause
    exit /b 1
)

cd /d "%INSTALL_DIR%"

REM --- 1. Check for updates from the dev branch on GitHub ---
set OLD_VERSION=unknown
for /f "usebackq tokens=* delims=" %%v in (`powershell -NoProfile -Command "(Get-Content version.json | ConvertFrom-Json).version" 2^>nul`) do set OLD_VERSION=%%v

if not exist ".git" (
    echo This folder is not a git repository. Skipping update check.
    goto :setup
)

echo Checking GitHub for updates on branch "%BRANCH%"...
git fetch origin %BRANCH% >nul 2>nul
if errorlevel 1 (
    echo Could not reach GitHub. Skipping update and starting the app as-is.
    goto :setup
)

for /f "usebackq tokens=* delims=" %%h in (`git rev-parse HEAD`) do set LOCAL_HASH=%%h
for /f "usebackq tokens=* delims=" %%h in (`git rev-parse origin/%BRANCH%`) do set REMOTE_HASH=%%h

if "%LOCAL_HASH%"=="%REMOTE_HASH%" (
    echo Already up to date ^(version %OLD_VERSION%^).
    goto :setup
)

echo Update found. Pulling latest changes from origin/%BRANCH%...

REM Reinstall dependencies only if requirements.txt is part of the update
git diff --name-only %LOCAL_HASH% %REMOTE_HASH% | findstr /i "requirements.txt" >nul
if not errorlevel 1 set NEEDS_INSTALL=1

git pull origin %BRANCH%
if errorlevel 1 (
    echo.
    echo ERROR: git pull failed. Resolve any local changes/conflicts and try again.
    pause
    exit /b 1
)

set NEW_VERSION=unknown
for /f "usebackq tokens=* delims=" %%v in (`powershell -NoProfile -Command "(Get-Content version.json | ConvertFrom-Json).version" 2^>nul`) do set NEW_VERSION=%%v

echo.
echo Updated from version %OLD_VERSION% to version %NEW_VERSION%.

:setup
echo.

REM --- 2. Reuse venv if it exists, otherwise create it ---
if exist "%VENV_DIR%\Scripts\activate.bat" (
    echo Using existing virtual environment.
    call "%VENV_DIR%\Scripts\activate.bat"
) else (
    echo No virtual environment found. Creating one...
    python -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo ERROR: Failed to create the virtual environment.
        echo Make sure Python is installed and available on PATH.
        pause
        exit /b 1
    )
    call "%VENV_DIR%\Scripts\activate.bat"
    set NEEDS_INSTALL=1
)

if "%NEEDS_INSTALL%"=="1" (
    echo Installing/refreshing dependencies...
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies.
        pause
        exit /b 1
    )
)

REM --- 3. Start the Flask app in its own window ---
echo.
echo Starting the app at %APP_URL% ...
start "%APP_TITLE%" cmd /k "cd /d "%INSTALL_DIR%" && call "%VENV_DIR%\Scripts\activate.bat" && python app.py"

REM Give Flask a few seconds to boot before opening the browser
timeout /t 3 /nobreak >nul

REM --- 4. Open in Chrome (fallback: default browser) ---
where chrome >nul 2>nul
if %errorlevel%==0 (
    start "" chrome "%APP_URL%"
) else if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" (
    start "" "%ProgramFiles%\Google\Chrome\Application\chrome.exe" "%APP_URL%"
) else if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" (
    start "" "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" "%APP_URL%"
) else if exist "%LocalAppData%\Google\Chrome\Application\chrome.exe" (
    start "" "%LocalAppData%\Google\Chrome\Application\chrome.exe" "%APP_URL%"
) else (
    echo Chrome not found. Opening in your default browser instead.
    start "" "%APP_URL%"
)

echo.
echo The app is running in a separate window. Close that window to stop it.

endlocal
