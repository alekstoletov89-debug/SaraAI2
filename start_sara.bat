@echo off
setlocal
chcp 65001 >nul
title SaraAI

set "ROOT=%~dp0"
set "PYTHON=%USERPROFILE%\SaraAI\.venv\Scripts\python.exe"

cd /d "%ROOT%"

echo ================================================
echo                 SARA AI
echo ================================================
echo.

if not exist "%PYTHON%" (
    echo [ERROR] Python environment not found:
    echo "%PYTHON%"
    echo.
    echo Expected virtual environment: %%USERPROFILE%%\SaraAI\.venv
    pause
    exit /b 1
)

if not exist "%ROOT%sara_agent.py" (
    echo [ERROR] sara_agent.py not found in:
    echo "%ROOT%"
    pause
    exit /b 1
)

if not exist "%ROOT%core\memory_commands.py" (
    echo [ERROR] Missing core\memory_commands.py
    echo The SaraAI2 repository does not contain the required core folder.
    echo Copy the working core folder from %%USERPROFILE%%\SaraAI\core into this folder first.
    pause
    exit /b 1
)

if not exist "%ROOT%core\semantic_memory.py" (
    echo [ERROR] Missing core\semantic_memory.py
    echo The semantic memory module is required by sara_agent.py.
    pause
    exit /b 1
)

where ollama >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Ollama command not found. Check Ollama installation.
) else (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "if (-not (Get-Process ollama -ErrorAction SilentlyContinue)) { Start-Process -WindowStyle Minimized -FilePath 'ollama' -ArgumentList 'serve' -ErrorAction SilentlyContinue; Start-Sleep -Seconds 2 }" >nul 2>&1
)

echo Checking Python syntax...
"%PYTHON%" -X utf8 -m py_compile "%ROOT%sara_agent.py" "%ROOT%tools.py" "%ROOT%tts.py"
if errorlevel 1 (
    echo [ERROR] Python syntax check failed. Sara was not started.
    pause
    exit /b 1
)

echo Starting Sara...
echo To exit Sara, type: exit
echo.
"%PYTHON%" -X utf8 "%ROOT%sara_agent.py"
set "EXITCODE=%ERRORLEVEL%"

echo.
if not "%EXITCODE%"=="0" (
    echo Sara exited with error code %EXITCODE%.
    pause
)
exit /b %EXITCODE%
