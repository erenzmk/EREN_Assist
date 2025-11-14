"""Einfaches Overlay-Fenster für Statusmeldungen."""
from __future__ import annotations

import threading
import tkinter as tk


class OverlayWindow:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.geometry("450x300+50+50")
        self.root.title("KI-Kumpel Overlay")
        self.root.configure(bg="#1E1E1E")

        self.text = tk.Text(
            self.root,
            bg="#1E1E1E",
            fg="white",
            wrap="word",
            relief="flat",
            font=("Segoe UI", 11),
        )
        self.text.pack(expand=True, fill="both")

        threading.Thread(target=self._run, daemon=True).start()

    def _run(self) -> None:
        self.root.mainloop()

    def show(self, message: str) -> None:
        self.text.delete(1.0, tk.END)
        self.text.insert(tk.END, message)
        self.root.lift()
        self.root.focus_force()
