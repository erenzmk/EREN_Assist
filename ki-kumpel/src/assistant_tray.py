"""Kompatibilitäts-Skript für den Tray."""
from __future__ import annotations

from bootstrap import ensure_project_root

ROOT_DIR = ensure_project_root()

from ui.tray import create_tray


if __name__ == "__main__":  # pragma: no cover - Einstiegspunkt
    create_tray()
