import json
import os
import re
import sys
from datetime import datetime

import requests

from core.memory_commands import handle_memory_command
from core.semantic_memory import search_memories
from tools import execute_tool, TOOLS


OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
MODEL = "qwen3.5:9b"

HISTORY_FILE = os.path.join(
    os.path.dirname(__file__),
    "memory",
    "dialogue_history.json"
)

MAX_HISTORY = 12
MAX_TOOL_STEPS = 3


# ============================================================
# HISTORY
# ============================================================

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []

    try:
        with open(
            HISTORY_FILE,
            "r",
            encoding="utf-8"
        ) as f:
            data = json.load(f)

        if isinstance(data, list):
            return data[-MAX_HISTORY:]

    except Exception:
        pass

    return []


def save_history(history):
    os.makedirs(
        os.path.dirname(HISTORY_FILE),
        exist_ok=True
    )

    with open(
        HISTORY_FILE,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            history[-MAX_HISTORY:],
            f,
            ensure_ascii=False,
            indent=2
        )


def add_history(role, content):
    history = load_history()

    history.append({
        "role": role,
        "content": content,
        "time": datetime.now().isoformat(
            timespec="seconds"
        )
    })

    save_history(history)


# ============================================================
# MEMORY
# ============================================================

def get_memory_context(query):
    try:
        results = search_memories(
            query,
            limit=8,
            min_score=0.80
        )

        if not results:
            return "РќРµС‚ РїРѕРґС…РѕРґСЏС‰РёС… РІРѕСЃРїРѕРјРёРЅР°РЅРёР№."

        lines = []

        for item in results:
            if isinstance(item, dict):
                text = (
                    item.get("value")
                    or item.get("text")
                    or str(item)
                )
            else:
                text = str(item)

            lines.append("- " + text)

        return "\n".join(lines)

    except Exception as e:
        return f"РџР°РјСЏС‚СЊ РІСЂРµРјРµРЅРЅРѕ РЅРµРґРѕСЃС‚СѓРїРЅР°: {e}"


# ============================================================
# QWEN
# ============================================================

def ollama_chat(messages, temperature=0.2):
    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": False,
        "think": False,
        "options": {
            "temperature": temperature
        }
    }

    response = requests.post(
        OLLAMA_URL,
        json=payload,
        timeout=180
    )

    response.raise_for_status()

    data = response.json()

    return data["message"]["content"].strip()


# ============================================================
# TOOL PLANNER
# ============================================================

PLANNER_SYSTEM = r"""
РўС‹ вЂ” РїР»Р°РЅРёСЂРѕРІС‰РёРє РёРЅСЃС‚СЂСѓРјРµРЅС‚РѕРІ Р»РѕРєР°Р»СЊРЅРѕРіРѕ Р°СЃСЃРёСЃС‚РµРЅС‚Р° РЎР°СЂР°.

РўРІРѕСЏ Р·Р°РґР°С‡Р° вЂ” РѕРїСЂРµРґРµР»РёС‚СЊ, РЅСѓР¶РЅРѕ Р»Рё РІС‹РїРѕР»РЅРёС‚СЊ РёРЅСЃС‚СЂСѓРјРµРЅС‚ РґР»СЏ РѕС‚РІРµС‚Р° РїРѕР»СЊР·РѕРІР°С‚РµР»СЋ.

Р”РѕСЃС‚СѓРїРЅС‹Рµ РёРЅСЃС‚СЂСѓРјРµРЅС‚С‹:

1. windows_open_program
РџР°СЂР°РјРµС‚СЂ:
{"name":"РєР°Р»СЊРєСѓР»СЏС‚РѕСЂ"}

Р”РѕРїСѓСЃС‚РёРјС‹Рµ РїСЂРѕРіСЂР°РјРјС‹:
cmd
powershell
РґРёСЃРїРµС‚С‡РµСЂ Р·Р°РґР°С‡
Р±Р»РѕРєРЅРѕС‚
РєР°Р»СЊРєСѓР»СЏС‚РѕСЂ
РїСЂРѕРІРѕРґРЅРёРє
РґРёСЃРїРµС‚С‡РµСЂ СѓСЃС‚СЂРѕР№СЃС‚РІ
РїР°РЅРµР»СЊ СѓРїСЂР°РІР»РµРЅРёСЏ

2. powershell
РџР°СЂР°РјРµС‚СЂ:
{"command":"..."}

РСЃРїРѕР»СЊР·СѓР№ С‚РѕР»СЊРєРѕ РґР»СЏ Р±РµР·РѕРїР°СЃРЅРѕР№ РґРёР°РіРЅРѕСЃС‚РёРєРё Рё РїРѕР»СѓС‡РµРЅРёСЏ РёРЅС„РѕСЂРјР°С†РёРё.
РќРµ СѓРґР°Р»СЏР№ С„Р°Р№Р»С‹, РЅРµ С„РѕСЂРјР°С‚РёСЂСѓР№ РґРёСЃРєРё, РЅРµ РІС‹РєР»СЋС‡Р°Р№ РєРѕРјРїСЊСЋС‚РµСЂ Рё РЅРµ РІС‹РїРѕР»РЅСЏР№ СЂР°Р·СЂСѓС€РёС‚РµР»СЊРЅС‹Рµ РґРµР№СЃС‚РІРёСЏ.

3. web_search
РџР°СЂР°РјРµС‚СЂ:
{"query":"..."}

РСЃРїРѕР»СЊР·СѓР№ РґР»СЏ РїРѕРёСЃРєР° Р°РєС‚СѓР°Р»СЊРЅРѕР№ РёРЅС„РѕСЂРјР°С†РёРё РІ РёРЅС‚РµСЂРЅРµС‚Рµ.

4. web_open
РџР°СЂР°РјРµС‚СЂ:
{"url":"https://..."}

РСЃРїРѕР»СЊР·СѓР№ РґР»СЏ РѕС‚РєСЂС‹С‚РёСЏ СЃР°Р№С‚Р°.

5. disk_free_space
РџР°СЂР°РјРµС‚СЂ:
{"drive":"C"}

РСЃРїРѕР»СЊР·СѓР№ РґР»СЏ РїРѕР»СѓС‡РµРЅРёСЏ С‚РѕС‡РЅРѕРіРѕ СЃРІРѕР±РѕРґРЅРѕРіРѕ РјРµСЃС‚Р° РЅР° РґРёСЃРєРµ.
РќРµ РїРµСЂРµСЃС‡РёС‚С‹РІР°Р№ Р·РЅР°С‡РµРЅРёРµ СЃР°РјРѕСЃС‚РѕСЏС‚РµР»СЊРЅРѕ вЂ” РёСЃРїРѕР»СЊР·СѓР№ РіРѕС‚РѕРІРѕРµ РїРѕР»Рµ result.

Р•СЃР»Рё РёРЅСЃС‚СЂСѓРјРµРЅС‚ РќР• РЅСѓР¶РµРЅ, РІРµСЂРЅРё:

{
  "tool": "none",
  "arguments": {}
}

Р•СЃР»Рё РёРЅСЃС‚СЂСѓРјРµРЅС‚ РЅСѓР¶РµРЅ, РІРµСЂРЅРё:

{
  "tool": "РЅР°Р·РІР°РЅРёРµ_РёРЅСЃС‚СЂСѓРјРµРЅС‚Р°",
  "arguments": {...}
}

РќРёРєР°РєРѕРіРѕ Markdown.
РќРёРєР°РєРёС… РїРѕСЏСЃРЅРµРЅРёР№.
РўРѕР»СЊРєРѕ JSON.
"""


def extract_json(text):
    text = text.strip()

    # РЈР±РёСЂР°РµРј markdown fence, РµСЃР»Рё Qwen РµРіРѕ РІСЃС‘-С‚Р°РєРё РґРѕР±Р°РІРёР».
    text = re.sub(
        r"^```(?:json)?",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"```$",
        "",
        text
    )

    text = text.strip()

    try:
        return json.loads(text)
    except Exception:
        pass

    match = re.search(
        r"\{.*\}",
        text,
        flags=re.DOTALL
    )

    if not match:
        return None

    try:
        return json.loads(match.group(0))
    except Exception:
        return None


def plan_tool(user_text, memory_context, history, tool_results=None):
    history_text = ""

    for item in history[-6:]:
        role = item.get("role", "")
        content = item.get("content", "")

        history_text += (
            f"{role}: {content}\n"
        )


    executed_context = json.dumps(tool_results or [], ensure_ascii=False)

    prompt = f"""
Текущая дата и время:
{datetime.now().strftime("%d.%m.%Y %H:%M:%S")}

Долговременная память:
{memory_context}

Недавний диалог:
{history_text}

Сообщение пользователя:
{user_text}

Уже выполненные инструменты:
{executed_context}

Если задача уже выполнена, верни только:
{{"tool":"none","arguments":{{}}}}

Иначе верни только JSON следующего инструмента.
Не повторяй успешно выполненный тот же вызов без новой причины.
"""


    try:
        result = ollama_chat(
            [
                {
                    "role": "system",
                    "content": PLANNER_SYSTEM
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0
        )

        data = extract_json(result)

        if not isinstance(data, dict):
            return {
                "tool": "none",
                "arguments": {}
            }

        tool = data.get("tool")

        if tool != "none" and tool not in TOOLS:
            return {
                "tool": "none",
                "arguments": {}
            }

        arguments = data.get(
            "arguments",
            {}
        )

        if not isinstance(arguments, dict):
            arguments = {}

        return {
            "tool": tool,
            "arguments": arguments
        }

    except Exception:
        return {
            "tool": "none",
            "arguments": {}
        }


# ============================================================
# FINAL ANSWER
# ============================================================

def build_final_prompt(
    user_text,
    memory_context,
    history,
    tool_results
):
    history_text = ""

    for item in history[-8:]:
        history_text += (
            f'{item.get("role")}: '
            f'{item.get("content")}\n'
        )

    results_text = ""

    if tool_results:
        results_text = json.dumps(
            tool_results,
            ensure_ascii=False,
            indent=2
        )
    else:
        results_text = "РРЅСЃС‚СЂСѓРјРµРЅС‚С‹ РЅРµ РёСЃРїРѕР»СЊР·РѕРІР°Р»РёСЃСЊ."

    return f"""
РўС‹ вЂ” РЎР°СЂР°, Р»РѕРєР°Р»СЊРЅС‹Р№ РїРµСЂСЃРѕРЅР°Р»СЊРЅС‹Р№ РїРѕРјРѕС‰РЅРёРє РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ.

РћС‚РІРµС‡Р°Р№ РїРѕ-СЂСѓСЃСЃРєРё.
Р“РѕРІРѕСЂРё РµСЃС‚РµСЃС‚РІРµРЅРЅРѕ, РєРѕСЂРѕС‚РєРѕ Рё РїРѕ РґРµР»Сѓ.
РќРµ РІС‹РґСѓРјС‹РІР°Р№ СЂРµР·СѓР»СЊС‚Р°С‚С‹ РёРЅСЃС‚СЂСѓРјРµРЅС‚РѕРІ.
Р•СЃР»Рё РёРЅС„РѕСЂРјР°С†РёРё РґРѕСЃС‚Р°С‚РѕС‡РЅРѕ вЂ” РЅРµ Р·Р°РґР°РІР°Р№ Р»РёС€РЅРёС… РІРѕРїСЂРѕСЃРѕРІ.

РўРµРєСѓС‰Р°СЏ РґР°С‚Р° Рё РІСЂРµРјСЏ:
{datetime.now().strftime("%d.%m.%Y %H:%M:%S")}

Р”РѕР»РіРѕРІСЂРµРјРµРЅРЅР°СЏ РїР°РјСЏС‚СЊ:
{memory_context}

РќРµРґР°РІРЅРёР№ РґРёР°Р»РѕРі:
{history_text}

РЎРѕРѕР±С‰РµРЅРёРµ РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ:
{user_text}

Р РµР·СѓР»СЊС‚Р°С‚С‹ РІС‹РїРѕР»РЅРµРЅРЅС‹С… РёРЅСЃС‚СЂСѓРјРµРЅС‚РѕРІ:
{results_text}

РўРµРїРµСЂСЊ РґР°Р№ РїРѕР»СЊР·РѕРІР°С‚РµР»СЋ РЅРѕСЂРјР°Р»СЊРЅС‹Р№ РµСЃС‚РµСЃС‚РІРµРЅРЅС‹Р№ РѕС‚РІРµС‚.
"""


def final_answer(
    user_text,
    memory_context,
    history,
    tool_results
):
    # Р•СЃР»Рё РёРЅСЃС‚СЂСѓРјРµРЅС‚ СЂРµР°Р»СЊРЅРѕ РІС‹РїРѕР»РЅРёР»СЃСЏ вЂ” РЅРµ РїРѕР·РІРѕР»СЏРµРј Qwen
    # РІС‹РґСѓРјС‹РІР°С‚СЊ СЂРµР·СѓР»СЊС‚Р°С‚. Р‘РµСЂС‘Рј С„Р°РєС‚РёС‡РµСЃРєРёР№ СЂРµР·СѓР»СЊС‚Р°С‚ РёРЅСЃС‚СЂСѓРјРµРЅС‚Р°.

    if tool_results:
        last = tool_results[-1]
        tool_name = last.get("tool")
        result = last.get("result", {})

        if isinstance(result, dict):
            if result.get("ok") is True:

                if tool_name == "windows_list_windows":
                    windows = result.get("windows", [])

                    if not windows:
                        return "РЎРµР№С‡Р°СЃ РѕС‚РєСЂС‹С‚С‹С… РѕРєРѕРЅ РЅРµ РЅР°Р№РґРµРЅРѕ."

                    titles = [
                        w.get("title", "").strip()
                        for w in windows
                        if w.get("title")
                    ]

                    if not titles:
                        return "РЎРµР№С‡Р°СЃ РѕС‚РєСЂС‹С‚С‹С… РѕРєРѕРЅ РЅРµ РЅР°Р№РґРµРЅРѕ."

                    return "РћС‚РєСЂС‹С‚С‹Рµ РѕРєРЅР°:\n" + "\n".join(
                        f"вЂў {title}" for title in titles
                    )

                direct_result = result.get("result")

                if direct_result:
                    return str(direct_result)

                return "Р“РѕС‚РѕРІРѕ."

            error = result.get("error")

            if error:
                return f"РќРµ РїРѕР»СѓС‡РёР»РѕСЃСЊ РІС‹РїРѕР»РЅРёС‚СЊ РєРѕРјР°РЅРґСѓ: {error}"

            return "РљРѕРјР°РЅРґР° РЅРµ РІС‹РїРѕР»РЅРµРЅР°."

    # Р•СЃР»Рё РёРЅСЃС‚СЂСѓРјРµРЅС‚РѕРІ РЅРµ Р±С‹Р»Рѕ вЂ” РѕР±С‹С‡РЅС‹Р№ РѕС‚РІРµС‚ Qwen.
    prompt = build_final_prompt(
        user_text,
        memory_context,
        history,
        tool_results
    )

    return ollama_chat(
        [
            {
                "role": "system",
                "content": (
                    "РўС‹ РЎР°СЂР°. "
                    "РћС‚РІРµС‡Р°Р№ РµСЃС‚РµСЃС‚РІРµРЅРЅРѕ РЅР° СЂСѓСЃСЃРєРѕРј СЏР·С‹РєРµ. "
                    "РќРµ РІС‹РґСѓРјС‹РІР°Р№ С„Р°РєС‚С‹ Рё СЂРµР·СѓР»СЊС‚Р°С‚С‹ РґРµР№СЃС‚РІРёР№."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.35
    )
# ============================================================
# AGENT
# ============================================================


# ============================================================
# FAST ROUTER
# ============================================================

def fast_route(user_text):
    """??????? ????????????? ??????? ????????? ??????."""
    text = user_text.strip().lower()

    if not text:
        return None

    # Windows audio
    if "\u043a\u0430\u043a\u0430\u044f \u0433\u0440\u043e\u043c\u043a\u043e\u0441\u0442\u044c" in text or "\u0443\u0440\u043e\u0432\u0435\u043d\u044c \u0433\u0440\u043e\u043c\u043a\u043e\u0441\u0442\u0438" in text:
        result = execute_tool("windows_audio", {"action": "status"})
        return result.get("result") if result.get("ok") else result.get("error")

    if "\u0432\u044b\u043a\u043b\u044e\u0447\u0438 \u0437\u0432\u0443\u043a" in text:
        result = execute_tool("windows_audio", {"action": "mute"})
        return result.get("result") if result.get("ok") else result.get("error")

    if "\u0432\u043a\u043b\u044e\u0447\u0438 \u0437\u0432\u0443\u043a" in text:
        result = execute_tool("windows_audio", {"action": "unmute"})
        return result.get("result") if result.get("ok") else result.get("error")

    if ("\u043f\u0440\u0438\u0431\u0430\u0432\u044c \u0433\u0440\u043e\u043c\u043a\u043e\u0441\u0442\u044c" in text
        or "\u0443\u0432\u0435\u043b\u0438\u0447\u044c \u0433\u0440\u043e\u043c\u043a\u043e\u0441\u0442\u044c" in text
        or "\u0441\u0434\u0435\u043b\u0430\u0439 \u043f\u043e\u0433\u0440\u043e\u043c\u0447\u0435" in text):
        result = execute_tool("windows_audio", {"action": "up", "value": 10})
        return result.get("result") if result.get("ok") else result.get("error")

    if ("\u0443\u0431\u0430\u0432\u044c \u0433\u0440\u043e\u043c\u043a\u043e\u0441\u0442\u044c" in text
        or "\u0443\u043c\u0435\u043d\u044c\u0448\u0438 \u0433\u0440\u043e\u043c\u043a\u043e\u0441\u0442\u044c" in text
        or "\u0441\u0434\u0435\u043b\u0430\u0439 \u043f\u043e\u0442\u0438\u0448\u0435" in text):
        result = execute_tool("windows_audio", {"action": "down", "value": 10})
        return result.get("result") if result.get("ok") else result.get("error")

    if "\u0433\u0440\u043e\u043c\u043a\u043e\u0441\u0442\u044c" in text:
        m = re.search(r"(\d{1,3})\s*%", text)
        if not m:
            m = re.search(r"\b(\d{1,3})\b", text)

        if m:
            level = max(0, min(100, int(m.group(1))))
            result = execute_tool("windows_audio", {"action": "set", "value": level})
            return result.get("result") if result.get("ok") else result.get("error")

    # ???????? ???????? ? ????????
    open_prefixes = (
        "\u043e\u0442\u043a\u0440\u043e\u0439 ",
        "\u0437\u0430\u043f\u0443\u0441\u0442\u0438 ",
        "\u043e\u0442\u043a\u0440\u044b\u0442\u044c ",
        "\u0437\u0430\u043f\u0443\u0441\u0442\u0438\u0442\u044c ",
    )

    for prefix in open_prefixes:
        if text.startswith(prefix):
            target = text[len(prefix):].strip()

            if target:
                settings_words = (
                    "\u043d\u0430\u0441\u0442\u0440\u043e\u0439\u043a\u0438",
                    "\u043f\u0430\u0440\u0430\u043c\u0435\u0442\u0440\u044b",
                    "\u0441\u0435\u0442\u044c",
                    "wifi",
                    "wi-fi",
                    "bluetooth",
                    "\u0437\u0432\u0443\u043a",
                    "\u044d\u043a\u0440\u0430\u043d",
                    "\u0434\u0438\u0441\u043f\u043b\u0435\u0439",
                    "\u043f\u0435\u0440\u0441\u043e\u043d\u0430\u043b\u0438\u0437\u0430\u0446\u0438\u044f",
                    "\u043e\u0431\u043d\u043e\u0432\u043b\u0435\u043d\u0438\u044f",
                    "\u043a\u043e\u043d\u0444\u0438\u0434\u0435\u043d\u0446\u0438\u0430\u043b\u044c\u043d\u043e\u0441\u0442\u044c",
                    "\u0443\u0447\u0435\u0442\u043d\u044b\u0435 \u0437\u0430\u043f\u0438\u0441\u0438",
                    "\u043f\u0440\u0438\u043b\u043e\u0436\u0435\u043d\u0438\u044f",
                    "\u0445\u0440\u0430\u043d\u0438\u043b\u0438\u0449\u0435",
                    "\u043c\u044b\u0448\u044c",
                    "\u043a\u043b\u0430\u0432\u0438\u0430\u0442\u0443\u0440\u0430",
                    "\u043a\u0430\u043c\u0435\u0440\u0430",
                    "\u043c\u0438\u043a\u0440\u043e\u0444\u043e\u043d",
                )

                if target in settings_words:
                    result = execute_tool(
                        "windows_open_settings",
                        {"name": target}
                    )
                else:
                    result = execute_tool(
                        "windows_open_any",
                        {"name": target}
                    )

                if result.get("ok"):
                    return result.get(
                        "result",
                        f"\u041e\u0442\u043a\u0440\u044b\u0442\u043e: {target}"
                    )

                return result.get(
                    "error",
                    f"\u041d\u0435 \u0443\u0434\u0430\u043b\u043e\u0441\u044c \u043e\u0442\u043a\u0440\u044b\u0442\u044c: {target}"
                )


    # ?????????? ?????????? WINDOWS
    if "????? ?????????" in text or "??????? ?????????" in text:
        result = execute_tool("windows_audio", {"action": "status"})
        return result.get("result") if result.get("ok") else result.get("error")

    if "??????? ????" in text or "??????? ???? ?????????" in text:
        result = execute_tool("windows_audio", {"action": "mute"})
        return result.get("result") if result.get("ok") else result.get("error")

    if "?????? ????" in text or "?????? ???? ???????" in text:
        result = execute_tool("windows_audio", {"action": "unmute"})
        return result.get("result") if result.get("ok") else result.get("error")

    if (
        "??????? ?????????" in text
        or "??????? ?????????" in text
        or "?????? ????????" in text
    ):
        result = execute_tool("windows_audio", {"action": "up", "value": 10})
        return result.get("result") if result.get("ok") else result.get("error")

    if (
        "????? ?????????" in text
        or "??????? ?????????" in text
        or "?????? ??????" in text
    ):
        result = execute_tool("windows_audio", {"action": "down", "value": 10})
        return result.get("result") if result.get("ok") else result.get("error")

    if "?????????" in text:
        m = re.search(r"(\d{1,3})\s*%", text)
        if not m:
            m = re.search(r"\b(\d{1,3})\b", text)

        if m:
            level = max(0, min(100, int(m.group(1))))
            result = execute_tool(
                "windows_audio",
                {"action": "set", "value": level}
            )
            return result.get("result") if result.get("ok") else result.get("error")

    # ???? WINDOWS
    if (
        ("\u043f\u043e\u043a\u0430\u0436\u0438 \u043e\u043a\u043d\u0430" in text or "\u043f\u043e\u043a\u0430\u0436\u0438 \u043e\u0442\u043a\u0440\u044b\u0442\u044b\u0435 \u043e\u043a\u043d\u0430" in text)
        or "\u0441\u043f\u0438\u0441\u043e\u043a \u043e\u043a\u043e\u043d" in text
        or "\u043a\u0430\u043a\u0438\u0435 \u043e\u043a\u043d\u0430" in text
    ):
        result = execute_tool("windows_list_windows", {})

        if result.get("ok"):
            windows = result.get("windows", [])

            if not windows:
                return "\u041e\u043a\u043d\u0430 \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d\u044b."

            return "\u041e\u0442\u043a\u0440\u044b\u0442\u044b\u0435 \u043e\u043a\u043d\u0430:\n" + "\n".join(
                f"- {w['title']}" for w in windows
            )

        return result.get(
            "error",
            "\u041d\u0435 \u0443\u0434\u0430\u043b\u043e\u0441\u044c \u043f\u043e\u043b\u0443\u0447\u0438\u0442\u044c \u0441\u043f\u0438\u0441\u043e\u043a \u043e\u043a\u043e\u043d."
        )

    window_actions = (
        ("\u0441\u0432\u0435\u0440\u043d\u0438 ", "\u0441\u0432\u0435\u0440\u043d\u0438"),
        ("\u0440\u0430\u0437\u0432\u0435\u0440\u043d\u0438 ", "\u0440\u0430\u0437\u0432\u0435\u0440\u043d\u0438"),
        ("\u0430\u043a\u0442\u0438\u0432\u0438\u0440\u0443\u0439 ", "\u0430\u043a\u0442\u0438\u0432\u0438\u0440\u0443\u0439"),
        ("\u043f\u0435\u0440\u0435\u043a\u043b\u044e\u0447\u0438\u0441\u044c \u043d\u0430 ", "\u043f\u0435\u0440\u0435\u043a\u043b\u044e\u0447\u0438\u0441\u044c"),
        ("\u0437\u0430\u043a\u0440\u043e\u0439 ", "\u0437\u0430\u043a\u0440\u043e\u0439"),
        ("\u0437\u0430\u043a\u0440\u044b\u0442\u044c ", "\u0437\u0430\u043a\u0440\u043e\u0439"),
        ("\u043c\u0430\u043a\u0441\u0438\u043c\u0438\u0437\u0438\u0440\u0443\u0439 ", "\u043c\u0430\u043a\u0441\u0438\u043c\u0438\u0437\u0438\u0440\u0443\u0439"),
    )

    for prefix, action in window_actions:
        if text.startswith(prefix):
            target = text[len(prefix):].strip()

            if not target:
                return "\u041d\u0435 \u0443\u043a\u0430\u0437\u0430\u043d\u043e, \u043a\u0430\u043a\u043e\u0435 \u043e\u043a\u043d\u043e \u043d\u0443\u0436\u043d\u043e \u0443\u043f\u0440\u0430\u0432\u043b\u044f\u0442\u044c."

            result = execute_tool(
                "windows_control_window",
                {
                    "action": action,
                    "target": target
                }
            )

            return result.get(
                "result",
                result.get(
                    "error",
                    "\u041d\u0435 \u0443\u0434\u0430\u043b\u043e\u0441\u044c \u0443\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u043e\u043a\u043d\u043e."
                )
            )


    # ???????? / ???????? CPU
    process_words = (
        "\u043f\u0440\u043e\u0446\u0435\u0441\u0441\u044b",
        "\u043f\u0440\u043e\u0446\u0435\u0441\u0441",
        "\u0446\u043f\u0443",
        "\u043f\u0440\u043e\u0446\u0435\u0441\u0441\u043e\u0440",
        "\u043d\u0430\u0433\u0440\u0443\u0437\u043a\u0430",
        "\u0436\u0440\u0435\u0442",
        "\u0436\u0440\u0443\u0442",
    )

    if any(word in text for word in process_words):
        result = execute_tool("windows_processes", {})

        if result.get("ok"):
            return (
                "\u0421\u0430\u043c\u044b\u0435 \u0430\u043a\u0442\u0438\u0432\u043d\u044b\u0435 \u043f\u0440\u043e\u0446\u0435\u0441\u0441\u044b:\n"
                + result.get("result", "")
            )

        return result.get(
            "error",
            "\u041d\u0435 \u0443\u0434\u0430\u043b\u043e\u0441\u044c \u043f\u043e\u043b\u0443\u0447\u0438\u0442\u044c \u0441\u043f\u0438\u0441\u043e\u043a \u043f\u0440\u043e\u0446\u0435\u0441\u0441\u043e\u0432."
        )

    # ????
    if "\u0434\u0438\u0441\u043a" in text:
        disk_words = (
            "\u043c\u0435\u0441\u0442\u0430",
            "\u0441\u0432\u043e\u0431\u043e\u0434",
            "\u043e\u0441\u0442\u0430\u043b\u043e\u0441\u044c",
            "\u0441\u043a\u043e\u043b\u044c\u043a\u043e",
        )

        if any(word in text for word in disk_words):
            drive = "C"

            for letter in ("c", "d", "e", "f"):
                if letter in text:
                    drive = letter.upper()
                    break

            result = execute_tool(
                "disk_free_space",
                {"drive": drive}
            )

            if result.get("ok"):
                return result.get(
                    "result",
                    f"\u041d\u0430 \u0434\u0438\u0441\u043a\u0435 {drive}: \u0441\u0432\u043e\u0431\u043e\u0434\u043d\u043e {result.get('free_gb')} \u0413\u0411."
                )

            return f"\u041d\u0435 \u0443\u0434\u0430\u043b\u043e\u0441\u044c \u043f\u0440\u043e\u0432\u0435\u0440\u0438\u0442\u044c \u0434\u0438\u0441\u043a {drive}."


    # ============================================================
    # FIXED UNIVERSAL ROUTES
    if "покажи информацию о системе" in text:
        result = execute_tool("windows_manager", {"action": "system"})
        return result.get("result") if result.get("ok") else result.get("error")

    if "покажи сеть" in text:
        result = execute_tool("windows_manager", {"action": "network", "network_action": "status"})
        return result.get("result") if result.get("ok") else result.get("error")

    if "покажи автозагрузку" in text:
        result = execute_tool("windows_manager", {"action": "startup"})
        return result.get("result") if result.get("ok") else result.get("error")

    if "покажи службы" in text:
        result = execute_tool("windows_manager", {"action": "service", "service_action": "list"})
        return result.get("result") if result.get("ok") else result.get("error")
    # UNIVERSAL WINDOWS MANAGER ROUTER
    # ============================================================

    if any(x in text for x in (
        "РёРЅС„РѕСЂРјР°С†РёСЏ Рѕ СЃРёСЃС‚РµРјРµ",
        "РёРЅС„РѕСЂРјР°С†РёСЋ Рѕ СЃРёСЃС‚РµРјРµ",
        "С…Р°СЂР°РєС‚РµСЂРёСЃС‚РёРєРё РєРѕРјРїСЊСЋС‚РµСЂР°",
        "С…Р°СЂР°РєС‚РµСЂРёСЃС‚РёРєРё РїРє",
        "РґР°РЅРЅС‹Рµ Рѕ РєРѕРјРїСЊСЋС‚РµСЂРµ",
        "РёРЅС„РѕСЂРјР°С†РёСЏ Рѕ РєРѕРјРїСЊСЋС‚РµСЂРµ",
        "СЃРІРµРґРµРЅРёСЏ Рѕ СЃРёСЃС‚РµРјРµ",
    )):
        result = execute_tool("windows_manager", {"action": "system"})
        return result.get("result") if result.get("ok") else result.get("error")

    if any(x in text for x in [
        "какой у меня ip", "какой у меня айпи", "мой ip", "мой айпи"
    ]):
        return execute_tool("windows_manager", {
            "action": "network",
            "network_action": "ip"
        })

    if any(x in text for x in (
        "РєР°РєРѕР№ Сѓ РјРµРЅСЏ ip",
        "РєР°РєРѕР№ Сѓ РјРµРЅСЏ Р°Р№РїРё",
        "РјРѕР№ ip",
        "РјРѕР№ Р°Р№РїРё",
        "РїРѕРєР°Р¶Рё СЃРµС‚СЊ",
        "СЃРѕСЃС‚РѕСЏРЅРёРµ СЃРµС‚Рё",
        "РёРЅС„РѕСЂРјР°С†РёСЏ Рѕ СЃРµС‚Рё",
        "СЃРѕСЃС‚РѕСЏРЅРёРµ РёРЅС‚РµСЂРЅРµС‚Р°",
        "СЃРѕСЃС‚РѕСЏРЅРёРµ wifi",
        "СЃРѕСЃС‚РѕСЏРЅРёРµ РІР°Р№С„Р°Р№",
        "РїРѕРєР°Р¶Рё wifi",
        "РїРѕРєР°Р¶Рё РІР°Р№С„Р°Р№",
    )):
        result = execute_tool(
            "windows_manager",
            {"action": "network", "network_action": "status"}
        )
        return result.get("result") if result.get("ok") else result.get("error")

    if any(x in text for x in (
        "РїРѕРєР°Р¶Рё Р°РІС‚РѕР·Р°РіСЂСѓР·РєСѓ",
        "С‡С‚Рѕ РІ Р°РІС‚РѕР·Р°РіСЂСѓР·РєРµ",
        "СЃРїРёСЃРѕРє Р°РІС‚РѕР·Р°РіСЂСѓР·РєРё",
        "РїСЂРѕРіСЂР°РјРјС‹ РІ Р°РІС‚РѕР·Р°РіСЂСѓР·РєРµ",
    )):
        result = execute_tool(
            "windows_manager",
            {"action": "startup"}
        )
        return result.get("result") if result.get("ok") else result.get("error")

    if any(x in text for x in (
        "РїРѕРєР°Р¶Рё СЃР»СѓР¶Р±С‹",
        "СЃРїРёСЃРѕРє СЃР»СѓР¶Р±",
        "СЃР»СѓР¶Р±С‹ windows",
        "СЃР»СѓР¶Р±С‹ РІРёРЅРґРѕРІСЃ",
    )):
        result = execute_tool(
            "windows_manager",
            {"action": "service", "service_action": "status"}
        )
        return result.get("result") if result.get("ok") else result.get("error")

    if text.startswith("РїСЂРѕРІРµСЂСЊ С„Р°Р№Р» "):
        file_path = text[len("РїСЂРѕРІРµСЂСЊ С„Р°Р№Р» "):].strip()

        if file_path:
            result = execute_tool(
                "windows_manager",
                {
                    "action": "file",
                    "file_action": "exists",
                    "path": file_path,
                }
            )
            return result.get("result") if result.get("ok") else result.get("error")

    if any(x in text for x in (
        "РІС‹РєР»СЋС‡Рё РєРѕРјРїСЊСЋС‚РµСЂ",
        "РІС‹РєР»СЋС‡Рё РїРє",
        "РїРµСЂРµР·Р°РіСЂСѓР·Рё РєРѕРјРїСЊСЋС‚РµСЂ",
        "РїРµСЂРµР·Р°РіСЂСѓР·Рё РїРє",
        "Р·Р°Р±Р»РѕРєРёСЂСѓР№ РєРѕРјРїСЊСЋС‚РµСЂ",
        "Р·Р°Р±Р»РѕРєРёСЂСѓР№ РїРє",
        "СѓСЃС‹РїРё РєРѕРјРїСЊСЋС‚РµСЂ",
        "СѓСЃС‹РїРё РїРє",
    )):
        if "РїРµСЂРµР·Р°РіСЂСѓР·Рё" in text:
            power_action = "restart"
        elif "Р·Р°Р±Р»РѕРєРёСЂСѓР№" in text:
            power_action = "lock"
        elif "СѓСЃС‹РїРё" in text:
            power_action = "sleep"
        else:
            power_action = "shutdown"

        result = execute_tool(
            "windows_manager",
            {
                "action": "power",
                "power_action": power_action,
            }
        )
        return result.get("result") if result.get("ok") else result.get("error")
    return None


# ============================================================
# UNIVERSAL ROUTER
# ============================================================

def _tool_result_text(result):
    if not isinstance(result, dict):
        return str(result)
    if result.get("ok"):
        return result.get("result") or "Готово."
    return result.get("error") or "Команда не выполнена."


def universal_route(user_text):
    """Быстрый слой для очевидных Windows-команд и явных запросов свежей информации."""
    text = user_text.strip().lower()
    if not text:
        return None

    # Составные запросы оставляем Qwen, чтобы можно было выполнить несколько действий.
    action_markers = (
        "открой ", "открыть ", "запусти ", "запустить ",
        "покажи ", "проверь ", "закрой ", "сверни ", "разверни ",
        "убей ", "заверши ", "переключись ", "активируй "
    )
    if text.count(" и ") >= 1 and sum(1 for x in action_markers if x in text) >= 2:
        return None

    web_markers = (
        "сегодня", "сейчас", "последние новости", "актуальные новости",
        "новости", "курс доллара", "курс евро", "погода",
        "сколько стоит сейчас", "цена сейчас",
    )
    if any(x in text for x in web_markers):
        return _tool_result_text(execute_tool("web_search", {"query": user_text}))

    if any(x in text for x in ("информация о системе", "информацию о системе",
        "характеристики компьютера", "характеристики пк",
        "данные о компьютере", "информация о компьютере")):
        return _tool_result_text(execute_tool("windows_manager", {"action": "system"}))

    if any(x in text for x in ("покажи процессы", "покажи процесс", "какие процессы",
        "что грузит процессор", "что грузит цпу", "нагрузка на процессор",
        "кто грузит процессор", "кто жрет процессор", "кто жрёт процессор")):
        return _tool_result_text(execute_tool("windows_manager", {"action": "processes"}))

    if "диск" in text and any(x in text for x in ("сколько", "свобод", "осталось", "места")):
        drive = "C"
        m = re.search(r"\b([c-f])\s*:?", text)
        if m:
            drive = m.group(1).upper()
        return _tool_result_text(execute_tool("windows_manager", {"action": "disk", "drive": drive}))

    if any(x in text for x in ("покажи сеть", "состояние сети", "состояние интернета",
        "информация о сети", "состояние wifi", "состояние вайфай",
        "покажи wifi", "покажи вайфай")):
        return _tool_result_text(execute_tool("windows_manager",
            {"action": "network", "network_action": "status"}))

    if any(x in text for x in ("какой у меня ip", "какой у меня айпи", "мой ip", "мой айпи")):
        return _tool_result_text(execute_tool("windows_manager",
            {"action": "network", "network_action": "ip"}))

    if any(x in text for x in ("покажи автозагрузку", "что в автозагрузке", "список автозагрузки")):
        return _tool_result_text(execute_tool("windows_manager", {"action": "startup"}))

    if any(x in text for x in ("покажи службы", "список служб", "службы windows", "службы виндовс")):
        return _tool_result_text(execute_tool("windows_manager",
            {"action": "service", "service_action": "list"}))

    m = re.match(r"^(?:проверь|проверить)\s+(?:файл|папку)\s+(.+)$", text)
    if m:
        return _tool_result_text(execute_tool("windows_manager",
            {"action": "file", "file_action": "exists", "path": m.group(1).strip()}))

    if any(x in text for x in ("заблокируй компьютер", "заблокируй пк", "заблокируй виндовс")):
        return _tool_result_text(execute_tool("windows_manager",
            {"action": "power", "power_action": "lock"}))

    if any(x in text for x in ("усыпи компьютер", "усыпи пк", "переведи компьютер в сон")):
        return _tool_result_text(execute_tool("windows_manager",
            {"action": "power", "power_action": "sleep"}))

    if any(x in text for x in ("выключи компьютер", "выключи пк", "перезагрузи компьютер", "перезагрузи пк")):
        action = "restart" if "перезагрузи" in text else "shutdown"
        return _tool_result_text(execute_tool("windows_manager",
            {"action": "power", "power_action": action}))

    m = re.match(r"^(?:убей|заверши)\s+(?:процесс\s+)?([a-zа-я0-9_.-]+)$", text)
    if m:
        return _tool_result_text(execute_tool("windows_manager",
            {"action": "kill_process", "name": m.group(1)}))

    m = re.match(r"^(?:убей|заверши)\s+pid\s+(\d+)$", text)
    if m:
        return _tool_result_text(execute_tool("windows_manager",
            {"action": "kill_pid", "pid": int(m.group(1))}))

    if any(x in text for x in ("покажи окна", "покажи открытые окна", "список окон", "какие окна открыты")):
        result = execute_tool("windows_manager", {"action": "windows"})
        if result.get("ok"):
            windows = result.get("windows", [])
            if not windows:
                return "Открытых окон не найдено."
            return "Открытые окна:\n" + "\n".join(
                f"- {w.get('title', '')}" for w in windows if w.get("title"))
        return _tool_result_text(result)

    for prefix, action in (("сверни ", "minimize"), ("разверни ", "maximize"),
        ("активируй ", "activate"), ("переключись на ", "activate"),
        ("закрой окно ", "close")):
        if text.startswith(prefix):
            target = text[len(prefix):].strip()
            if target:
                return _tool_result_text(execute_tool("windows_manager",
                    {"action": "window", "window_action": action, "target": target}))

    for prefix in ("открой ", "открыть ", "запусти ", "запустить "):
        if text.startswith(prefix):
            target = text[len(prefix):].strip()
            if target:
                return _tool_result_text(execute_tool("windows_manager",
                    {"action": "open", "name": target}))

    return None

def process(user_text):
    user_text = user_text.strip()

    if not user_text:
        return ""

    # Р‘С‹СЃС‚СЂС‹Р№ РјР°СЂС€СЂСѓС‚ вЂ” СЂР°РЅСЊС€Рµ РїР°РјСЏС‚Рё, E5 Рё Qwen.
    fast_result = fast_route(user_text)

    if fast_result:
        add_history(
            "user",
            user_text
        )

        add_history(
            "assistant",
            fast_result
        )

        return fast_result

    # РўРѕР»СЊРєРѕ РµСЃР»Рё РєРѕРјР°РЅРґР° РЅРµ Р±С‹СЃС‚СЂР°СЏ вЂ” РїСЂРѕРІРµСЂСЏРµРј РєРѕРјР°РЅРґС‹ РїР°РјСЏС‚Рё.

    universal_result = universal_route(user_text)

    if universal_result:
        add_history("user", user_text)
        add_history("assistant", universal_result)
        return universal_result

    memory_result = handle_memory_command(
        user_text
    )

    if memory_result:
        add_history(
            "user",
            user_text
        )

        add_history(
            "assistant",
            memory_result
        )

        return memory_result

    history = load_history()

    memory_context = get_memory_context(
        user_text
    )

    tool_results = []


    # Qwen может выполнить цепочку до MAX_TOOL_STEPS инструментов.
    for step in range(MAX_TOOL_STEPS):
        plan = plan_tool(user_text, memory_context, history, tool_results)

        tool_name = plan.get("tool")
        arguments = plan.get("arguments", {})

        if tool_name == "none":
            break

        if any(
            item.get("tool") == tool_name
            and item.get("arguments") == arguments
            and item.get("result", {}).get("ok") is True
            for item in tool_results
        ):
            break

        result = execute_tool(tool_name, arguments)

        tool_results.append({
            "step": step + 1,
            "tool": tool_name,
            "arguments": arguments,
            "result": result
        })

        if not isinstance(result, dict) or not result.get("ok"):
            break


    answer = final_answer(
        user_text,
        memory_context,
        history,
        tool_results
    )

    add_history(
        "user",
        user_text
    )

    add_history(
        "assistant",
        answer
    )

    return answer


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 50)
    print("              SARA AI AGENT")
    print("=" * 50)
    print()
    print(f"РњРѕРґРµР»СЊ: {MODEL}")
    print("РџР°РјСЏС‚СЊ: SQLite + E5")
    print("РСЃС‚РѕСЂРёСЏ: РІРєР»СЋС‡РµРЅР°")
    print("РђРІС‚РѕРЅРѕРјРЅС‹Рµ РёРЅСЃС‚СЂСѓРјРµРЅС‚С‹: РІРєР»СЋС‡РµРЅС‹")
    print()
    print("Р”Р»СЏ РІС‹С…РѕРґР°: exit")
    print()

    while True:
        try:
            user_text = input("РўС‹: ").strip()

        except (KeyboardInterrupt, EOFError):
            print()
            break

        if user_text.lower() in {
            "exit",
            "quit",
            "РІС‹С…РѕРґ"
        }:
            break

        if not user_text:
            continue

        try:
            answer = process(
                user_text
            )

            print(
                "РЎР°СЂР°:",
                answer
            )
            print()

        except Exception as e:
            print(
                "РЎР°СЂР°: РћС€РёР±РєР° Р°РіРµРЅС‚Р°:",
                e
            )
            print()


if __name__ == "__main__":
    main()















