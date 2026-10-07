# coding: utf-8
"""
Local Qwen3-TTS voice for SaraAI.
Preset voice: Serena. No voice cloning.
The model is loaded lazily on the first response and kept in memory.
"""
import os
import tempfile
import threading
import time

_TTS = None
_TTS_LOCK = threading.Lock()

MODEL_PATH = os.getenv(
    "SARA_TTS_MODEL",
    "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice",
)
SPEAKER = "Serena"
LANGUAGE = "Russian"


def _load():
    global _TTS

    if _TTS is not None:
        return _TTS

    with _TTS_LOCK:
        if _TTS is not None:
            return _TTS

        import torch
        from qwen_tts import Qwen3TTSModel

        if not torch.cuda.is_available():
            raise RuntimeError("CUDA для Qwen3-TTS недоступна.")

        t0 = time.perf_counter()
        _TTS = Qwen3TTSModel.from_pretrained(
            MODEL_PATH,
            device_map="cuda:0",
            dtype=torch.bfloat16,
            attn_implementation="sdpa",
        )
        print(f"[TTS] Загрузка модели: {time.perf_counter() - t0:.2f} сек.")

    return _TTS


def speak(text):
    """Generate and immediately play Sara's response. Returns True on success."""
    text = str(text or "").strip()

    if not text:
        return False

    if len(text) > 1800:
        text = text[:1800].rsplit(" ", 1)[0] + "..."

    try:
        import soundfile as sf
        import winsound

        tts = _load()

        t0 = time.perf_counter()
        wavs, sr = tts.generate_custom_voice(
            text=text,
            language=LANGUAGE,
            speaker=SPEAKER,
            instruct="Говори естественно, тепло и спокойно, как персональный голосовой помощник.",
            max_new_tokens=512,
        )
        generation_time = time.perf_counter() - t0
        print(f"[TTS] Генерация: {generation_time:.2f} сек.")

        with tempfile.NamedTemporaryFile(
            suffix=".wav",
            prefix="sara_tts_",
            delete=False,
        ) as f:
            path = f.name

        try:
            t0 = time.perf_counter()
            sf.write(path, wavs[0], sr)
            winsound.PlaySound(path, winsound.SND_FILENAME)
            print(f"[TTS] Сохранение + воспроизведение: {time.perf_counter() - t0:.2f} сек.")
        finally:
            try:
                os.remove(path)
            except OSError:
                pass

        return True

    except Exception as e:
        print(f"[TTS] Ошибка: {e}")
        return False
