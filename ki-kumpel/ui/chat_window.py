"""Modernes Chat-Fenster mit Dark-Theme."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

_BG = "#1E1E1E"
_BG_USER = "#2E7D32"
_BG_ASSISTANT = "#1565C0"
_BG_SYSTEM = "#424242"
_TEXT_COLOR = "#FFFFFF"
_FONT = ("Segoe UI", 11)


class ChatWindow(ttk.Frame):
    def __init__(self, master: tk.Misc, *, on_send) -> None:
        super().__init__(master, padding=12)
        self.configure(style="Chat.TFrame")
        self._on_send = on_send

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Chat.TFrame", background=_BG)
        style.configure("ChatBubbleUser.TLabel", background=_BG_USER, foreground=_TEXT_COLOR, font=_FONT, padding=8)
        style.configure("ChatBubbleAssistant.TLabel", background=_BG_ASSISTANT, foreground=_TEXT_COLOR, font=_FONT, padding=8)
        style.configure("ChatBubbleSystem.TLabel", background=_BG_SYSTEM, foreground=_TEXT_COLOR, font=_FONT, padding=8)
        style.configure("ChatInput.TFrame", background=_BG)
        style.configure("Status.TLabel", background=_BG, foreground="#B0BEC5", font=("Segoe UI", 9))

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self.status_var = tk.StringVar(value="Bereit – OpenAI online")
        status_label = ttk.Label(self, textvariable=self.status_var, style="Status.TLabel")
        status_label.grid(row=0, column=0, sticky="we", pady=(0, 8))

        self.canvas = tk.Canvas(self, background=_BG, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.grid(row=1, column=0, sticky="nsew")
        self.scrollbar.grid(row=1, column=1, sticky="ns")

        self.messages_frame = ttk.Frame(self.canvas, style="Chat.TFrame")
        self.messages_frame.columnconfigure(0, weight=1)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.messages_frame, anchor="nw")

        self.messages_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        input_frame = ttk.Frame(self, style="ChatInput.TFrame")
        input_frame.grid(row=2, column=0, columnspan=2, sticky="we", pady=(12, 0))
        input_frame.columnconfigure(0, weight=1)

        self.input = tk.Text(input_frame, height=3, wrap="word", font=_FONT, background="#263238", foreground=_TEXT_COLOR, insertbackground=_TEXT_COLOR, relief="flat", padx=10, pady=10)
        self.input.grid(row=0, column=0, sticky="we")
        self.input.bind("<Return>", self._on_return)
        self.input.bind("<Shift-Return>", self._on_shift_return)

        send_button = ttk.Button(input_frame, text="Senden", command=self._trigger_send)
        send_button.grid(row=0, column=1, padx=(8, 0), sticky="e")

    def _on_frame_configure(self, event) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.after_idle(self._scroll_to_end)

    def _on_canvas_configure(self, event) -> None:
        width = event.width
        self.canvas.itemconfig(self.canvas_window, width=width)

    def _scroll_to_end(self) -> None:
        self.canvas.yview_moveto(1.0)

    def _on_return(self, event) -> str:
        if event.state & 0x0001:  # Shift
            return "break"
        self._trigger_send()
        return "break"

    def _on_shift_return(self, event) -> str:
        self.input.insert("insert", "\n")
        return "break"

    def _trigger_send(self) -> None:
        text = self.input.get("1.0", "end").strip()
        if not text:
            return
        self.input.delete("1.0", "end")
        self._on_send(text)

    def append_message(self, role: str, message: str) -> None:
        role = role.lower()
        if role == "user":
            style = "ChatBubbleUser.TLabel"
            anchor = "e"
        elif role == "assistant":
            style = "ChatBubbleAssistant.TLabel"
            anchor = "w"
        else:
            style = "ChatBubbleSystem.TLabel"
            anchor = "w"

        bubble = ttk.Label(self.messages_frame, text=message, style=style, wraplength=600, justify="left")
        bubble.grid(sticky=anchor, padx=8, pady=4)
        self.messages_frame.update_idletasks()
        self._scroll_to_end()

    def set_status(self, text: str) -> None:
        self.status_var.set(text)
