"""Hauptanwendung für den KI-Kumpel."""
from __future__ import annotations

import threading
import tkinter as tk
from tkinter import ttk

from core.config import AUTO_SCREENSHOT_INTERVAL_MS
from core.logger import get_logger
from core.router import AssistantRouter
from core.screen_capture import capture_all_screens, cleanup_screenshots
from ui.chat_window import ChatWindow

_logger = get_logger(__name__)


class KIKumpelApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("KI-Kumpel")
        self.root.geometry("980x720")
        self.root.configure(bg="#1E1E1E")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.router = AssistantRouter()

        container = ttk.Frame(root, padding=12)
        container.pack(fill="both", expand=True)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(1, weight=1)

        toolbar = ttk.Frame(container)
        toolbar.grid(row=0, column=0, sticky="we", pady=(0, 8))
        toolbar.columnconfigure(0, weight=1)

        self.chat_window = ChatWindow(container, on_send=self._on_user_text)
        self.chat_window.grid(row=1, column=0, sticky="nsew")

        button_frame = ttk.Frame(container)
        button_frame.grid(row=2, column=0, sticky="we", pady=(12, 0))

        self.btn_ask_screen = ttk.Button(
            button_frame,
            text="🔍 Bildschirm + Frage",
            command=self._on_request_screen,
        )
        self.btn_ask_screen.pack(side="left")

        self.btn_ask_text = ttk.Button(
            button_frame,
            text="❓ Nur Frage",
            command=self._on_request_text,
        )
        self.btn_ask_text.pack(side="left", padx=(8, 0))

        self.btn_cleanup = ttk.Button(
            button_frame,
            text="🧹 Screenshots leeren",
            command=self._on_cleanup,
        )
        self.btn_cleanup.pack(side="left", padx=(8, 0))

        self.btn_quit = ttk.Button(button_frame, text="Beenden", command=self.on_close)
        self.btn_quit.pack(side="right")

        self.chat_window.append_message(
            "system",
            "KI-Kumpel bereit. Stelle eine Frage oder verwende die Buttons für Screenshots.",
        )

        self.root.after(2000, self._auto_loop)

    def _set_buttons_state(self, state: str) -> None:
        for button in (self.btn_ask_screen, self.btn_ask_text, self.btn_cleanup, self.btn_quit):
            button.configure(state=state)

    def _on_user_text(self, text: str) -> None:
        self.chat_window.append_message("user", text)
        self._start_worker(self.router.handle_text, text)

    def _on_request_text(self) -> None:
        text = self.chat_window.input.get("1.0", "end").strip()
        if not text:
            self.chat_window.append_message("system", "Bitte gib zuerst eine Frage ein.")
            return
        self.chat_window.input.delete("1.0", "end")
        self.chat_window.append_message("user", text)
        self._start_worker(self.router.handle_text, text)

    def _on_request_screen(self) -> None:
        question = self.chat_window.input.get("1.0", "end").strip()
        if not question:
            self.chat_window.append_message("system", "Bitte beschreibe deine Frage, bevor ein Screenshot erstellt wird.")
            return
        self.chat_window.input.delete("1.0", "end")
        self.chat_window.append_message("user", question)

        def worker() -> None:
            try:
                shots = capture_all_screens()
                if not shots:
                    raise RuntimeError("Kein Monitor erkannt")
                _, image = shots[0]
                answer = self.router.handle_vision(question, image)
            except Exception as exc:
                _logger.exception("Fehler bei Vision-Anfrage")
                answer = f"Fehler bei der Analyse: {exc}"
            self._post_answer(answer)

        self._set_buttons_state("disabled")
        threading.Thread(target=worker, daemon=True).start()

    def _on_cleanup(self) -> None:
        removed = cleanup_screenshots()
        self.chat_window.append_message("system", f"Screenshots entfernt ({removed} Dateien).")

    def _start_worker(self, func, *args) -> None:
        self._set_buttons_state("disabled")

        def worker() -> None:
            try:
                answer = func(*args)
            except Exception as exc:
                _logger.exception("Fehler bei Anfrage")
                answer = f"Fehler bei der Anfrage: {exc}"
            self._post_answer(answer)

        threading.Thread(target=worker, daemon=True).start()

    def _post_answer(self, answer: str) -> None:
        def _update() -> None:
            self.chat_window.append_message("assistant", answer)
            self._set_buttons_state("normal")

        self.root.after(0, _update)

    def _auto_loop(self) -> None:
        def worker() -> None:
            try:
                shots = capture_all_screens()
                if shots:
                    self.chat_window.append_message(
                        "system",
                        f"Auto-Screenshot gespeichert ({len(shots)} Monitor(e)).",
                    )
            except Exception as exc:
                _logger.error("Auto-Screenshot fehlgeschlagen: %s", exc)

        threading.Thread(target=worker, daemon=True).start()
        self.root.after(AUTO_SCREENSHOT_INTERVAL_MS, self._auto_loop)

    def on_close(self) -> None:
        try:
            self.router.cleanup()
        finally:
            self.root.destroy()


def main() -> None:
    root = tk.Tk()
    app = KIKumpelApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
