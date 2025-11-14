"""Kompatibilitäts-Einstiegspunkt für die neue Architektur."""
from __future__ import annotations

from bootstrap import ensure_project_root

ROOT_DIR = ensure_project_root()

from ui.app import main


if __name__ == "__main__":  # pragma: no cover - Einstiegspunkt
    main()
