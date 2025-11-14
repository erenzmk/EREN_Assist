"""Kompatibilitäts-Overlay."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ui.overlay import OverlayWindow


def main() -> None:
    OverlayWindow()


if __name__ == "__main__":  # pragma: no cover
    main()
