@echo off
setlocal enabledelayedexpansion
title Push to GitHub - AutoRoute AI

echo ======================================================================
echo           Push Project to GitHub - AutoRoute AI
echo ======================================================================
echo.

:: 1. Navigate to script directory
cd /d "%~dp0"

:: 2. Check if Git is installed
where git >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Git is not installed or not in your system PATH.
    echo Please install Git from: https://git-scm.com/downloads
    echo.
    pause
    exit /b 1
)

:: 3. Check Git user.name and user.email
for /f "delims=" %%i in ('git config user.name 2^>nul') do set "GIT_USER=%%i"
for /f "delims=" %%i in ('git config user.email 2^>nul') do set "GIT_EMAIL=%%i"

if "%GIT_USER%"=="" (
    echo [INFO] Git user.name is not configured.
    set /p "GIT_USER=Enter your Git / GitHub username [default: pushkarjain989]: "
    if "!GIT_USER!"=="" set "GIT_USER=pushkarjain989"
    git config --global user.name "!GIT_USER!"
    echo [OK] Set user.name to !GIT_USER!
)

if "%GIT_EMAIL%"=="" (
    echo [INFO] Git user.email is not configured.
    set /p "GIT_EMAIL=Enter your Git / GitHub email: "
    if "!GIT_EMAIL!"=="" (
        set "GIT_EMAIL=!GIT_USER!@users.noreply.github.com"
        echo [INFO] Using fallback noreply email: !GIT_EMAIL!
    )
    git config --global user.email "!GIT_EMAIL!"
    echo [OK] Set user.email to !GIT_EMAIL!
)
echo.

:: 4. Check if Git repo is initialized
if not exist ".git" (
    echo [1/4] Initializing Git repository...
    git init -b main
) else (
    echo [1/4] Git repository found.
)

:: 5. Configure remote repository
set "REPO_URL=https://github.com/pushkarjain989/Intelligent_Customer_Complaint_Routing.git"
git remote get-url origin >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [2/4] Setting remote origin to %REPO_URL%...
    git remote add origin %REPO_URL%
) else (
    echo [2/4] Remote origin already configured.
    git remote set-url origin %REPO_URL%
)

:: 6. Stage and commit changes
echo [3/4] Staging files...
git add .

:: Check if there are changes to commit
git status --porcelain | findstr /R "." >nul
if %ERRORLEVEL% equ 0 (
    set /p "COMMIT_MSG=Enter commit message (Press Enter for default): "
    if "!COMMIT_MSG!"=="" set "COMMIT_MSG=Update: Project sync %date% %time%"
    git commit -m "!COMMIT_MSG!"
) else (
    echo No new changes to commit.
)

:: 7. Push to GitHub
echo.
echo [4/4] Pushing to GitHub (main branch)...
echo NOTE: If a GitHub login dialog or browser window appears,
echo       please sign in with your GitHub account (pushkarjain989).
echo ======================================================================
echo.

git branch -M main
git push -u origin main

if %ERRORLEVEL% equ 0 (
    echo.
    echo ======================================================================
    echo  [SUCCESS] Project successfully pushed to GitHub!
    echo  View repository: %REPO_URL%
    echo ======================================================================
) else (
    echo.
    echo ======================================================================
    echo  [PUSH FAILED] Could not push to GitHub.
    echo.
    echo  Common causes & solutions:
    echo  1. Authentication:
    echo     - GitHub no longer accepts account passwords via HTTPS.
    echo     - When prompted for Password, use a Personal Access Token (PAT).
    echo     - Generate PAT at: https://github.com/settings/tokens
    echo       (Select scopes: 'repo')
    echo  2. Remote conflict:
    echo     - If the remote has new commits, run: git pull origin main --rebase
    echo  3. Repository access:
    echo     - Ensure you are logged into account 'pushkarjain989'.
    echo ======================================================================
)

echo.
pause
