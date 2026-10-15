@echo off
setlocal EnableExtensions
chcp 65001 >nul
title Установка SaraAI2
set "ROOT=%~dp0"
set "PY=%ROOT%.venv\Scripts\python.exe"
echo ================================================
echo          УСТАНОВКА SARA AI 2
echo ================================================
echo.
if not exist "%ROOT%sara2_local.py" (
  echo Ошибка: не найден sara2_local.py. Распакуй весь ZIP в одну папку.
  pause
  exit /b 2
)
if not exist "%ROOT%requirements-sara2.txt" (
  echo Ошибка: не найден requirements-sara2.txt.
  pause
  exit /b 2
)
where py >nul 2>&1
if errorlevel 1 (
  echo Не найден Python Launcher. Установи Python 3.11 или 3.12 с python.org и включи Python Launcher.
  pause
  exit /b 2
)
if not exist "%PY%" (
  py -3.11 -m venv "%ROOT%.venv"
  if errorlevel 1 (
    if exist "%ROOT%.venv" rmdir /s /q "%ROOT%.venv"
    py -3.12 -m venv "%ROOT%.venv"
  )
)
if not exist "%PY%" (
  echo Не удалось создать виртуальное окружение Python 3.11/3.12.
  echo Проверь установку Python и повтори запуск.
  pause
  exit /b 3
)
"%PY%" -c "import sys; print('Python:', sys.version); raise SystemExit(0 if sys.version_info[:2] in ((3,11),(3,12)) else 1)"
if errorlevel 1 (
  echo Виртуальное окружение создано на неподдерживаемой версии Python.
  echo Удали папку .venv и установи Python 3.11 или 3.12.
  pause
  exit /b 3
)
"%PY%" -m pip install --upgrade pip
if errorlevel 1 goto fail
"%PY%" -m pip install -r "%ROOT%requirements-sara2.txt"
if errorlevel 1 goto fail
"%PY%" -m py_compile "%ROOT%sara2_local.py"
if errorlevel 1 goto fail
set "SARA_ROOT=%ROOT%"
set "SARA_ICON=%SystemRoot%\System32\shell32.dll,220"
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $desktop=[Environment]::GetFolderPath('Desktop'); if ([string]::IsNullOrWhiteSpace($desktop)) { throw 'Не удалось определить папку рабочего стола' }; $shortcut=Join-Path $desktop 'SaraAI2.lnk'; $w=New-Object -ComObject WScript.Shell; $s=$w.CreateShortcut($shortcut); $s.TargetPath=(Join-Path $env:SARA_ROOT 'START_SARA2.bat'); $s.WorkingDirectory=$env:SARA_ROOT; $s.IconLocation=$env:SARA_ICON; $s.Description='SaraAI2 local assistant'; $s.Save(); if (-not (Test-Path $shortcut)) { throw 'Ярлык не создан' }" 
if errorlevel 1 goto fail
echo.
echo Установка и проверка синтаксиса завершены.
echo Ярлык SaraAI2 создан на рабочем столе.
echo Важно: это промежуточная текстовая сборка, не полный голосовой контур.
echo Ollama и модель qwen3.5:9b должны быть установлены отдельно.
echo Если возникла ошибка, запусти CHECK_SARA2.bat и пришли SARA2_DIAGNOSTICS.txt.
echo Память проекта и история известных проблем: SARA2_PROJECT_MEMORY.md
echo.
pause
exit /b 0
:fail
echo.
echo Установка или проверка завершилась с ошибкой. См. сообщение выше.
pause
exit /b 1
