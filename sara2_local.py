import json
import os
import subprocess
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent
MEMORY = ROOT / "memory" / "dialogue_history.json"
OLLAMA_URL = os.environ.get("SARA_OLLAMA_URL", "http://127.0.0.1:11434/api/chat")
OLLAMA_TAGS_URL = OLLAMA_URL.rsplit("/", 2)[0] + "/api/tags"
MODEL = os.environ.get("SARA_MODEL", "qwen3.5:9b")
MAX_HISTORY = 12

PROGRAMS = {
    "калькулятор": "calc.exe",
    "блокнот": "notepad.exe",
    "проводник": "explorer.exe",
    "диспетчер задач": "taskmgr.exe",
    "панель управления": "control.exe",
    "параметры": "ms-settings:",
    "настройки сети": "ms-settings:network",
    "настройки звука": "ms-settings:sound",
    "настройки bluetooth": "ms-settings:bluetooth",
}


def load_history():
    try:
        data = json.loads(MEMORY.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            return []
        return [item for item in data if isinstance(item, dict)][-MAX_HISTORY:]
    except (OSError, ValueError):
        return []


def save_history(history):
    MEMORY.parent.mkdir(parents=True, exist_ok=True)
    temporary = MEMORY.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(history[-MAX_HISTORY:], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    temporary.replace(MEMORY)


def fast_command(text):
    q = text.strip().lower()
    for phrase, target in PROGRAMS.items():
        if q in ("открой " + phrase, "запусти " + phrase, "открыть " + phrase, "запустить " + phrase):
            try:
                if target.startswith("ms-settings:"):
                    os.startfile(target)
                else:
                    subprocess.Popen([target], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return "Открываю: " + phrase
            except Exception as e:
                return "Не удалось открыть " + phrase + ": " + str(e)
    if q in ("покажи процессы", "список процессов", "какие процессы запущены"):
        try:
            p = subprocess.run(["tasklist"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=15)
            return p.stdout[:9000] if p.returncode == 0 else (p.stderr or "Команда tasklist завершилась с ошибкой.")
        except Exception as e:
            return "Ошибка получения процессов: " + str(e)
    if q in ("информация о системе", "сведения о системе", "покажи систему"):
        try:
            p = subprocess.run(["systeminfo"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=25)
            return p.stdout[:9000] if p.returncode == 0 else (p.stderr or "Команда systeminfo завершилась с ошибкой.")
        except Exception as e:
            return "Ошибка получения сведений: " + str(e)
    return None


def ask_qwen(text, history):
    messages = [{
        "role": "system",
        "content": "Ты Сара, локальный помощник Windows. Отвечай по-русски, кратко и честно. Ты не можешь выполнять действия в Windows, если для них нет отдельной команды. Не утверждай, что сделала то, чего не делала."
    }]
    for item in history[-10:]:
        if isinstance(item, dict) and item.get("role") in ("user", "assistant") and item.get("content"):
            messages.append({"role": item["role"], "content": str(item["content"])})
    messages.append({"role": "user", "content": text})
    response = requests.post(OLLAMA_URL, json={
        "model": MODEL, "messages": messages, "stream": False,
        "think": False, "options": {"temperature": 0.35}
    }, timeout=180)
    response.raise_for_status()
    data = response.json()
    content = data.get("message", {}).get("content")
    if not isinstance(content, str) or not content.strip():
        raise ValueError("Ollama вернула пустой или неожиданный ответ.")
    return content.strip()


def check_ollama():
    try:
        response = requests.get(OLLAMA_TAGS_URL, timeout=3)
        response.raise_for_status()
        models = [m.get("name", "") for m in response.json().get("models", [])]
        if MODEL not in models:
            print("ПРЕДУПРЕЖДЕНИЕ: точная модель", MODEL, "не найдена в Ollama.")
            print("Доступные модели:", ", ".join(models) or "нет")
            return False
        print("Ollama доступна; модель найдена:", MODEL)
        return True
    except Exception as e:
        print("ПРЕДУПРЕЖДЕНИЕ: Ollama не отвечает:", str(e))
        return False


def main():
    print("=" * 48)
    print("SARA AI 2 — локальный текстовый режим")
    print("Модель:", MODEL)
    print("Голос жены пока отключён. Выход: exit")
    print("=" * 48)
    check_ollama()
    history = load_history()
    while True:
        try:
            text = input("\nТы: ").strip()
        except (KeyboardInterrupt, EOFError):
            print()
            break
        if text.lower() in ("exit", "quit", "выход"):
            break
        if not text:
            continue
        answer = fast_command(text)
        if answer is None:
            try:
                answer = ask_qwen(text, history)
            except Exception as e:
                answer = "Не удалось получить ответ от Ollama. Проверь, что Ollama запущена и модель скачана. Подробности: " + str(e)
        print("\nСара:", answer)
        history.extend([{"role": "user", "content": text}, {"role": "assistant", "content": answer}])
        history = history[-MAX_HISTORY:]
        try:
            save_history(history)
        except OSError as e:
            print("Предупреждение: не удалось сохранить историю:", e)


if __name__ == "__main__":
    main()
