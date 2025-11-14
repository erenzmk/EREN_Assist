"""Wrapper für Text-to-Speech."""
from __future__ import annotations

import threading
from typing import Optional

import pyttsx3

from core.logger import get_logger

_logger = get_logger(__name__)

try:
    _tts_engine: Optional[pyttsx3.Engine] = pyttsx3.init()
except Exception as exc:  # pragma: no cover - Initialisierung kann auf CI scheitern
    _logger.warning("TTS konnte nicht initialisiert werden: %s", exc)
    _tts_engine = None


def speak(text: str) -> None:
    if not _tts_engine:
        return

    def _run() -> None:
        try:
            assert _tts_engine is not None
            _tts_engine.say(text)
            _tts_engine.runAndWait()
        except Exception as exc:  # pragma: no cover - nur im Runtime-Fall relevant
            _logger.error("Fehler beim Sprechen: %s", exc)

    threading.Thread(target=_run, daemon=True).start()
