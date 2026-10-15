@echo off
setlocal EnableExtensions
chcp 65001 >nul
title SaraAI2 — голосовой запуск
set "ROOT=%~dp0"
cd /d "%ROOT%"

echo ================================================
echo            SARA AI 2 — VOICE START
echo ================================================
echo.

rem Prefer an environment installed inside this project.
set "PYTHON=%ROOT%.venv\Scripts\python.exe"
if not exist "%PYTHON%" set "PYTHON=%USERPROFILE%\SaraAI2\.venv\Scripts\python.exe"

if not exist "%PYTHON%" (
  echo [STOP] Не найден Python проекта.
  echo Ожидаемый путь: "%ROOT%.venv\Scripts\python.exe"
  echo Этот репозиторий пока не содержит полного установщика зависимостей.
  echo Ничего не изменено и установка не запускалась.
  pause
  exit /b 2
)

if not exist "%ROOT%sara_voice_agent.py" (
  echo [STOP] В репозитории отсутствует sara_voice_agent.py.
  echo Запуск текстового sara_agent.py вместо голосового намеренно запрещён.
  echo Нужен исходный голосовой модуль и локальный образец голоса жены.
  pause
  exit /b 3
)

if not exist "%ROOT%core\memory_commands.py" (
  echo [STOP] Не найден core\memory_commands.py.
  echo Репозиторий неполный: голосовой запуск пока нельзя считать рабочим.
  pause
  exit /b 4
)
if not exist "%ROOT%core\semantic_memory.py" (
  echo [STOP] Не найден core\semantic_memory.py.
  echo Репозиторий неполный: модуль памяти отсутствует.
  pause
  exit /b 5
)

"%PYTHON%" -X utf8 -c "import ast,pathlib,sys; files=[pathlib.Path(r'%ROOT%sara_voice_agent.py'),pathlib.Path(r'%ROOT%sara_agent.py'),pathlib.Path(r'%ROOT%tools.py')]; [(ast.parse(p.read_text(encoding='utf-8-sig'),filename=str(p))) for p in files if p.exists()]; print('Проверка синтаксиса пройдена')"
if errorlevel 1 (
  echo [STOP] Ошибка синтаксиса Python. Сара не запущена.
  pause
  exit /b 6
)

where ollama >nul 2>&1
if errorlevel 1 echo [WARNING] Ollama не найдена в PATH. Проверь её установку.

echo Запускаю голосовую Сару...
"%PYTHON%" -X utf8 "%ROOT%sara_voice_agent.py"
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" (
  echo.
  echo SaraAI2 завершилась с кодом %RC%.
  pause
)
exit /b %RC%
