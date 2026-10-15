@echo off
setlocal
chcp 65001 >nul
title SaraAI2
set "ROOT=%~dp0"
set "PY=%ROOT%.venv\Scripts\python.exe"
if not exist "%PY%" (
 echo Сначала запусти INSTALL_SARA2.bat.
 pause
 exit /b 2
)
cd /d "%ROOT%"
"%PY%" -X utf8 "%ROOT%sara2_local.py"
if errorlevel 1 (
 echo.
 echo SaraAI2 завершилась с ошибкой.
 pause
)
