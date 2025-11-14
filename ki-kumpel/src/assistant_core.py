"""CLI-Einstiegspunkt für schnelle Vision-Abfragen."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.screen_capture import capture_all_screens
from core.router import AssistantRouter


def run_assistant() -> None:
    router = AssistantRouter()
    shots = capture_all_screens()
    if not shots:
        raise RuntimeError("Kein Monitor gefunden")
    _, image = shots[0]
    answer = router.handle_vision("Beschreibe den Screenshot.", image)
    print("\n===== KI ANTWORT =====\n")
    print(answer)
    print("\n======================\n")


if __name__ == "__main__":  # pragma: no cover - CLI Einstieg
    run_assistant()
