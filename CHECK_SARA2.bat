@echo off
setlocal EnableExtensions
chcp 65001 >nul
title SaraAI2 - диагностика
set "ROOT=%~dp0"
set "OUT=%ROOT%SARA2_DIAGNOSTICS.txt"
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Continue'; $root=$env:ROOT; $out=$env:OUT; 'SARA AI 2 DIAGNOSTICS' | Set-Content -LiteralPath $out -Encoding UTF8; ('Date: ' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz')) | Add-Content -LiteralPath $out; ('Folder: ' + $root) | Add-Content -LiteralPath $out; ('OS: ' + (Get-CimInstance Win32_OperatingSystem).Caption + ' / ' + [Environment]::OSVersion.VersionString) | Add-Content -LiteralPath $out; '' | Add-Content -LiteralPath $out; '--- Required files ---' | Add-Content -LiteralPath $out; @('sara2_local.py','sara_agent.py','tools.py','tts.py','requirements-sara2.txt','INSTALL_SARA2.bat','START_SARA2.bat','core\memory_commands.py','core\semantic_memory.py','speech\listen.py','sara_voice_agent.py') | ForEach-Object { $p=Join-Path $root $_; (('{0}: {1}' -f $_, (Test-Path -LiteralPath $p))) | Add-Content -LiteralPath $out }; '' | Add-Content -LiteralPath $out; '--- Python launcher / versions ---' | Add-Content -LiteralPath $out; (& py -0p 2>&1 | Out-String) | Add-Content -LiteralPath $out; if (Test-Path (Join-Path $root '.venv\Scripts\python.exe')) { (& (Join-Path $root '.venv\Scripts\python.exe') --version 2>&1 | Out-String) | Add-Content -LiteralPath $out } else { 'Local .venv Python: MISSING' | Add-Content -LiteralPath $out }; '' | Add-Content -LiteralPath $out; '--- Ollama API / exact model ---' | Add-Content -LiteralPath $out; try { $tags=Invoke-RestMethod -Uri 'http://127.0.0.1:11434/api/tags' -TimeoutSec 4; $names=@($tags.models | ForEach-Object { $_.name }); ('Ollama API: OK' ) | Add-Content -LiteralPath $out; ('Models: ' + ($names -join ', ')) | Add-Content -LiteralPath $out; ('qwen3.5:9b exact match: ' + ($names -contains 'qwen3.5:9b')) | Add-Content -LiteralPath $out } catch { ('Ollama API: ERROR - ' + $_.Exception.Message) | Add-Content -LiteralPath $out }; '' | Add-Content -LiteralPath $out; '--- Installed packages in local .venv ---' | Add-Content -LiteralPath $out; $vp=Join-Path $root '.venv\Scripts\python.exe'; if (Test-Path $vp) { (& $vp -m pip show requests qwen-tts torch faster-whisper 2>&1 | Out-String) | Add-Content -LiteralPath $out } else { 'Skipped: local .venv is absent.' | Add-Content -LiteralPath $out }; 'Done.' | Add-Content -LiteralPath $out; Write-Host ('Diagnostic log saved: ' + $out)";
if exist "%OUT%" (
  echo.
  echo Диагностика сохранена:
  echo "%OUT%"
  echo Пришли мне этот файл, и я продолжу разбор по результатам.
) else (
  echo Не удалось создать диагностический файл. Проверь PowerShell.
)
pause
