"""Hilfsfunktionen zum Auffinden des Projektwurzelverzeichnisses."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable


DEFAULT_MARKERS: tuple[str, ...] = ("core", "ui")


def _candidate_roots(start: Path) -> list[Path]:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        frozen_base = Path(sys._MEIPASS)  # type: ignore[attr-defined]
        return [frozen_base]
    return [start, *start.parents]


def ensure_project_root(markers: Iterable[str] = DEFAULT_MARKERS) -> Path:
    start = Path(__file__).resolve().parent
    marker_set = tuple(markers)

    for candidate in _candidate_roots(start):
        if all((candidate / marker).exists() for marker in marker_set):
            root = candidate
            break
    else:
        root = start

    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)

    return root


__all__ = ["ensure_project_root"]
