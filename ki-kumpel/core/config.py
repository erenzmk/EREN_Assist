"""Zentrale Konfigurationswerte und Pfaddefinitionen."""
from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / "logs"
SCREENSHOT_DIR = BASE_DIR / "screenshots"
DOCS_DIR = BASE_DIR / "docs"

for directory in (DATA_DIR, LOG_DIR, SCREENSHOT_DIR, DOCS_DIR):
    directory.mkdir(parents=True, exist_ok=True)

MEMORY_DB_PATH = DATA_DIR / "memory.sqlite"

MODEL_VISION = os.getenv("KI_KUMPEL_MODEL_VISION", "gpt-4o-mini")
MODEL_TEXT = os.getenv("KI_KUMPEL_MODEL_TEXT", "gpt-4o-mini")

AUTO_SCREENSHOT_INTERVAL_MS = int(os.getenv("KI_KUMPEL_AUTO_INTERVAL_MS", "20000"))

STYLE_SAMPLE_DIR = DATA_DIR / "style_samples"
STYLE_SAMPLE_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_SYSTEM_PROMPT_VISION = (
    "Du bist ein persönlicher Desktop-Assistent. "
    "Du siehst einen Screenshot des Nutzers und sollst konkret, kurz und praxisnah helfen."
)
DEFAULT_SYSTEM_PROMPT_TEXT = (
    "Du bist ein hilfreicher Assistent für einen IT-/Dispatch-Spezialisten. "
    "Antworte kurz, klar und konkret."
)

LOG_FILE = LOG_DIR / "ki_kumpel.log"
PROGRESS_LOG_FILE = DOCS_DIR / "PROGRESS.md"
