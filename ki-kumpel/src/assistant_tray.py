"""Kompatibilitäts-Skript für den Tray."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ui.tray import create_tray


if __name__ == "__main__":  # pragma: no cover - Einstiegspunkt
    create_tray()
