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
where py >nul 2>&1
if errorlevel 1 (
  echo Не найден Python Launcher. Установи Python 3.11 или 3.12 с python.org и включи Add Python to PATH.
  pause
  exit /b 2
)
if not exist "%PY%" (
  py -3.11 -m venv "%ROOT%.venv"
  if errorlevel 1 py -3 -m venv "%ROOT%.venv"
)
if not exist "%PY%" (
  echo Не удалось создать виртуальное окружение.
  pause
  exit /b 3
)
"%PY%" -m pip install --upgrade pip
if errorlevel 1 goto fail
"%PY%" -m pip install -r "%ROOT%requirements-sara2.txt"
if errorlevel 1 goto fail
if not exist "%ROOT%START_SARA2.bat" (
  echo Не найден START_SARA2.bat.
  pause
  exit /b 4
)
set "SARA_SHORTCUT=%USERPROFILE%\Desktop\SaraAI2.lnk"
set "SARA_TARGET=%ROOT%START_SARA2.bat"
set "SARA_ICON=%SystemRoot%\System32\shell32.dll,220"
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$w=New-Object -ComObject WScript.Shell; $s=$w.CreateShortcut($env:SARA_SHORTCUT); $s.TargetPath=$env:SARA_TARGET; $s.WorkingDirectory=$env:USERPROFILE; $s.IconLocation=$env:SARA_ICON; $s.Description='SaraAI2 local assistant'; $s.Save()"
if errorlevel 1 goto fail
echo.
echo Установка завершена. Ярлык SaraAI2 создан на рабочем столе.
echo Важно: Ollama и модель qwen3.5:9b должны быть установлены отдельно.
echo.
pause
exit /b 0
:fail
echo.
echo Установка завершилась с ошибкой. См. сообщение выше.
pause
exit /b 1
