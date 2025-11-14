"""System-Tray-Integration für den KI-Kumpel."""
from __future__ import annotations

import os
import sys
import threading

import pystray
from PIL import Image
from pystray import MenuItem as item
import tkinter as tk
from tkinter import messagebox, simpledialog

from core.logger import get_logger
from core.router import AssistantRouter
from core.screen_capture import capture_all_screens

_logger = get_logger(__name__)


def _resource_path(relative: str) -> str:
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative)
    return os.path.join(os.path.abspath("."), relative)


def _ask_text(router: AssistantRouter) -> None:
    root = tk.Tk()
    root.withdraw()
    text = simpledialog.askstring("KI-Kumpel", "Text eingeben:")
    if not text:
        root.destroy()
        return

    def worker() -> None:
        try:
            answer = router.handle_text(text)
            messagebox.showinfo("KI-Antwort", answer)
        except Exception as exc:
            _logger.exception("Tray-Textanfrage fehlgeschlagen")
            messagebox.showerror("Fehler", str(exc))
        finally:
            root.destroy()

    threading.Thread(target=worker, daemon=True).start()


def _send_screenshot(router: AssistantRouter) -> None:
    root = tk.Tk()
    root.withdraw()
    question = simpledialog.askstring("KI-Kumpel", "Frage zum Screenshot:")
    if not question:
        root.destroy()
        return

    def worker() -> None:
        try:
            shots = capture_all_screens()
            if not shots:
                raise RuntimeError("Kein Monitor gefunden")
            _, image = shots[0]
            answer = router.handle_vision(question, image)
            messagebox.showinfo("KI-Antwort", answer)
        except Exception as exc:
            _logger.exception("Tray-Vision-Anfrage fehlgeschlagen")
            messagebox.showerror("Fehler", str(exc))
        finally:
            root.destroy()

    threading.Thread(target=worker, daemon=True).start()


def create_tray() -> None:
    router = AssistantRouter()

    icon_path = _resource_path("assets/ChatGPT.ico")
    try:
        icon_image = Image.open(icon_path)
    except Exception as exc:
        _logger.error("Tray-Icon konnte nicht geladen werden: %s", exc)
        raise SystemExit(1) from exc

    def on_quit(icon, _item) -> None:  # pragma: no cover - UI Interaktion
        icon.stop()
        router.cleanup()

    menu = (
        item("Screenshot an KI senden", lambda: _send_screenshot(router)),
        item("Text an KI senden", lambda: _ask_text(router)),
        item("Beenden", on_quit),
    )

    icon = pystray.Icon("KI-Kumpel", icon_image, "KI-Kumpel", menu)
    _logger.info("Tray gestartet")
    icon.run()


if __name__ == "__main__":
    create_tray()
