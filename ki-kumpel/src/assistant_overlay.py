"""Kompatibilitäts-Overlay."""
from __future__ import annotations

from bootstrap import ensure_project_root

ROOT_DIR = ensure_project_root()

from ui.overlay import OverlayWindow


def main() -> None:
    OverlayWindow()


if __name__ == "__main__":  # pragma: no cover
    main()
