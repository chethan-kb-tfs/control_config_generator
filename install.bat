@echo off
REM ============================================================
REM install.bat
REM First-time setup.
REM   1. Clones the repo into a fixed, predictable location:
REM        %USERPROFILE%\control_config_generator
REM      (i.e. C:\Users\<you>\control_config_generator)
REM      If it's already cloned there, this step is skipped.
REM   2. Creates the virtual environment (if missing).
REM   3. Installs dependencies.
REM Safe to re-run at any time.
REM
REM run.bat and update.bat both assume the app lives at this same
REM fixed location, so always use install.bat first.
REM ============================================================
setlocal

set REPO_URL=https://github.com/chethan-kb-tfs/control_config_generator.git
set BRANCH=dev
set INSTALL_DIR=%USERPROFILE%\control_config_generator
set VENV_DIR=%INSTALL_DIR%\venv

echo ==============================================
echo  Databricks SQL Insert Generator - Install
echo ==============================================
echo  Install location: %INSTALL_DIR%
echo.

REM --- Make sure git is available ---
where git >nul 2>nul
if errorlevel 1 (
    echo ERROR: git is not installed or not on PATH.
    echo Install Git for Windows from https://git-scm.com/download/win and try again.
    pause
    exit /b 1
)

REM --- Make sure python is available ---
where python >nul 2>nul
if errorlevel 1 (
    echo ERROR: python is not installed or not on PATH.
    echo Install Python from https://www.python.org/downloads/ and try again.
    pause
    exit /b 1
)

REM --- 1. Clone the repo if it isn't already there ---
if exist "%INSTALL_DIR%\.git" (
    echo Repo already cloned at "%INSTALL_DIR%". Skipping clone.
    echo ^(Use update.bat later to pull the latest changes.^)
) else (
    if exist "%INSTALL_DIR%" (
        echo ERROR: "%INSTALL_DIR%" already exists but is not a git repository.
        echo Remove or rename that folder, then run install.bat again.
        pause
        exit /b 1
    )
    echo Cloning %REPO_URL% ^(branch: %BRANCH%^) into "%INSTALL_DIR%"...
    git clone -b %BRANCH% "%REPO_URL%" "%INSTALL_DIR%"
    if errorlevel 1 (
        echo.
        echo ERROR: git clone failed. Check your network connection and the repo URL.
        pause
        exit /b 1
    )
)

cd /d "%INSTALL_DIR%"

REM --- 2. Create the virtual environment if it doesn't exist ---
if exist "%VENV_DIR%\Scripts\activate.bat" (
    echo Virtual environment already exists. Skipping creation.
) else (
    echo Creating virtual environment...
    python -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo.
        echo ERROR: Failed to create the virtual environment.
        pause
        exit /b 1
    )
)

echo.
echo Activating virtual environment...
call "%VENV_DIR%\Scripts\activate.bat"

REM --- 3. Install dependencies ---
echo.
echo Installing dependencies from requirements.txt...
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo ERROR: Failed to install dependencies.
    pause
    exit /b 1
)

echo.
echo ==============================================
echo  Install complete.
echo  App installed at: %INSTALL_DIR%
echo  Run run.bat from there any time to start the app.
echo ==============================================
pause

endlocal
