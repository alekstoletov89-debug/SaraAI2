@echo off
setlocal
chcp 65001 >nul
title SaraAI2 - сбор исходников
set "PS1=%TEMP%\collect_sara2_sources_%RANDOM%.ps1"
> "%PS1%" echo $ErrorActionPreference = 'Stop'
>> "%PS1%" echo $roots = @("$env:USERPROFILE\SaraAI", "$env:USERPROFILE\SaraAI2") ^| Where-Object { Test-Path $_ }
>> "%PS1%" echo if (-not $roots) { Write-Host "Не найдены папки SaraAI или SaraAI2 в профиле пользователя."; Read-Host "Enter"; exit 2 }
>> "%PS1%" echo $out = Join-Path $env:USERPROFILE "Desktop\SaraAI2_SOURCE_BUNDLE"
>> "%PS1%" echo if (Test-Path $out) { Remove-Item $out -Recurse -Force }
>> "%PS1%" echo New-Item -ItemType Directory -Path $out ^| Out-Null
>> "%PS1%" echo $allowed = @("*.py","*.bat","*.ps1","*.txt","*.toml","*.yaml","*.yml","*.ini","*.cfg")
>> "%PS1%" echo $dirs = @("core","speech","tools","ui","voice","tests")
>> "%PS1%" echo $files = @("sara.py","sara_agent.py","sara_voice_agent.py","sara2_local.py","tts.py","listen.py","requirements.txt","requirements-sara2.txt","requirements-minimal.txt","start_sara.bat","START_SARA2.bat","INSTALL_SARA2.bat","README.md")
>> "%PS1%" echo foreach ($root in $roots) {
>> "%PS1%" echo   $label = Split-Path $root -Leaf
>> "%PS1%" echo   $dest = Join-Path $out $label
>> "%PS1%" echo   New-Item -ItemType Directory -Path $dest ^| Out-Null
>> "%PS1%" echo   foreach ($name in $files) { $src = Join-Path $root $name; if (Test-Path $src -PathType Leaf) { Copy-Item $src $dest -Force } }
>> "%PS1%" echo   foreach ($dir in $dirs) { $src = Join-Path $root $dir; if (Test-Path $src -PathType Container) { Get-ChildItem $src -Recurse -File ^| Where-Object { $allowed -contains ("*" + $_.Extension) -and $_.FullName -notmatch '\\(\.venv|venv|__pycache__|models|memory|\.git)\\' } ^| ForEach-Object { $target = Join-Path $dest $_.FullName.Substring($root.Length + 1); New-Item -ItemType Directory -Path (Split-Path $target) -Force ^| Out-Null; Copy-Item $_.FullName $target -Force } } }
>> "%PS1%" echo }
>> "%PS1%" echo @("Source bundle for SaraAI2","Collected from: " + ($roots -join "; "),"Only source/config text files are included.","Excluded: virtual environments, models, memory/history, .git and all audio files.") ^| Set-Content (Join-Path $out "CONTENTS.txt") -Encoding UTF8
>> "%PS1%" echo $zip = Join-Path $env:USERPROFILE "Desktop\SaraAI2_SOURCE_BUNDLE.zip"
>> "%PS1%" echo if (Test-Path $zip) { Remove-Item $zip -Force }
>> "%PS1%" echo Compress-Archive -Path (Join-Path $out "*") -DestinationPath $zip -Force
>> "%PS1%" echo Write-Host ""
>> "%PS1%" echo Write-Host "Готово. Архив исходников: $zip"
>> "%PS1%" echo Write-Host "Проверь архив перед отправкой. В него не включаются аудио, модели и история диалогов."
>> "%PS1%" echo Read-Host "Нажми Enter для закрытия"
powershell -NoProfile -ExecutionPolicy Bypass -File "%PS1%"
set "RC=%ERRORLEVEL%"
del "%PS1%" >nul 2>&1
exit /b %RC%
