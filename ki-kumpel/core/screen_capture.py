"""Hilfsfunktionen zum Erfassen von Screenshots."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Tuple

import mss
from PIL import Image

from core.config import SCREENSHOT_DIR
from core.logger import log_line

ScreenshotInfo = Tuple[Path, Image.Image]


def capture_all_screens() -> List[ScreenshotInfo]:
    """Erzeugt Screenshots aller Monitore und speichert sie temporär."""
    results: List[ScreenshotInfo] = []
    with mss.mss() as sct:
        for idx, monitor in enumerate(sct.monitors[1:], start=1):
            raw = sct.grab(monitor)
            img = Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}_m{idx}.png"
            path = SCREENSHOT_DIR / filename
            img.save(path, "PNG")
            results.append((path, img))
    log_line(f"Auto-Screenshots erstellt: {len(results)}")
    return results


def cleanup_screenshots() -> int:
    """Löscht alle gespeicherten Screenshots und gibt die Anzahl zurück."""
    count = 0
    for file_path in SCREENSHOT_DIR.glob("*.png"):
        try:
            file_path.unlink()
            count += 1
        except OSError:
            continue
    log_line(f"Screenshots gelöscht: {count}")
    return count
