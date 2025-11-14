import os
import io
import base64
import threading
from datetime import datetime

import mss
from PIL import Image
from openai import OpenAI

import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

import pyttsx3

# ==============================
#   KONFIGURATION
# ==============================

MODEL_VISION = "gpt-4o-mini"   # Text + Bild
MODEL_TEXT = "gpt-4o-mini"     # nur Text (kann auch so bleiben)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LOG_DIR = os.path.join(BASE_DIR, "logs")
SCREENSHOT_DIR = os.path.join(BASE_DIR, "screenshots")

os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, "ki_kumpel.log")

AUTO_INTERVAL_MS = 20_000  # 20 Sekunden


# ==============================
#   OPENAI & TTS
# ==============================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError(
        "OPENAI_API_KEY ist nicht gesetzt. "
        "Bitte als Umgebungsvariable setzen."
    )

client = OpenAI(api_key=OPENAI_API_KEY)

try:
    tts_engine = pyttsx3.init()
except Exception:
    tts_engine = None


def speak(text: str):
    """Antwort vorlesen (falls TTS verfügbar)."""
    if not tts_engine:
        return

    def _run():
        try:
            tts_engine.say(text)
            tts_engine.runAndWait()
        except Exception:
            pass

    threading.Thread(target=_run, daemon=True).start()


# ==============================
#   HILFSFUNKTIONEN
# ==============================

def log_line(text: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {text}\n")


def capture_all_screens() -> list[tuple[str, Image.Image]]:
    """
    Screenshots ALLER Monitore.
    Rückgabe: Liste (pfad, image).
    """
    results = []
    with mss.mss() as sct:
        # monitors[0] = virtuell, ab 1 echte Monitore
        for idx, mon in enumerate(sct.monitors[1:], start=1):
            raw = sct.grab(mon)
            img = Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")

            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{ts}_m{idx}.png"
            path = os.path.join(SCREENSHOT_DIR, filename)
            img.save(path, "PNG")

            results.append((path, img))
    return results


def pil_to_base64_png(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")


def ask_vision(question: str, screenshot_img: Image.Image) -> str:
    img_b64 = pil_to_base64_png(screenshot_img)
    log_line(f"USER Frage+Screen: {question}")

    messages = [
        {
            "role": "system",
            "content": (
                "Du bist ein persönlicher Desktop-Assistent. "
                "Du siehst einen Screenshot des Nutzers und sollst "
                "konkret, kurz und praxisnah helfen."
            ),
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": (
                        "Hier ist ein Screenshot meines Bildschirms. "
                        "Nutze ihn zur Beantwortung der Frage. "
                        "Frage: " + question
                    ),
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "data:image/png;base64," + img_b64,
                    },
                },
            ],
        },
    ]

    resp = client.chat.completions.create(
        model=MODEL_VISION,
        messages=messages,
        temperature=0.3,
    )
    answer = resp.choices[0].message.content
    log_line(f"ASSISTANT Antwort: {answer}")
    return answer


def ask_text_only(question: str) -> str:
    log_line(f"USER Frage (nur Text): {question}")
    resp = client.chat.completions.create(
        model=MODEL_TEXT,
        messages=[
            {
                "role": "system",
                "content": (
                    "Du bist ein hilfreicher Assistent für einen "
                    "IT-/Dispatch-Spezialisten. Antworte kurz, klar und konkret."
                ),
            },
            {"role": "user", "content": question},
        ],
        temperature=0.3,
    )
    answer = resp.choices[0].message.content
    log_line(f"ASSISTANT Antwort: {answer}")
    return answer


# ==============================
#   GUI-APP
# ==============================

class KIKumpelApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("KI-Kumpel")
        self.root.geometry("900x650")

        try:
            icon_path = os.path.join(
                os.path.dirname(__file__),
                "assets",
                "ChatGPT.ico"
            )
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except Exception:
            pass

        self.build_ui()

        # Auto-Loop starten (Screenshots alle 20 Sekunden)
        self.root.after(2000, self.auto_loop)  # ersten Lauf nach 2s

        self.append_chat(
            "SYSTEM",
            "KI-Kumpel bereit. Schreibe eine Frage und klicke "
            "auf „Bildschirm + Frage“ oder „Nur Frage“.\n"
        )
        speak("Hallo Eren. Der KI-Kumpel ist bereit.")

    # ---- UI ----

    def build_ui(self):
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)

        main = ttk.Frame(self.root, padding=8)
        main.grid(row=0, column=0, sticky="nsew")
        main.rowconfigure(0, weight=1)
        main.columnconfigure(0, weight=1)

        # Chat
        self.chat = ScrolledText(
            main, wrap="word", state="disabled", font=("Segoe UI", 10)
        )
        self.chat.grid(row=0, column=0, columnspan=4, sticky="nsew", pady=(0, 8))

        # Eingabe
        self.entry = tk.Text(main, height=3, font=("Segoe UI", 10))
        self.entry.grid(row=1, column=0, columnspan=4, sticky="ew")

        # Buttons
        self.btn_ask_screen = ttk.Button(
            main, text="🔍 Bildschirm + Frage", command=self.on_ask_screen
        )
        self.btn_ask_screen.grid(row=2, column=0, sticky="w", pady=6)

        self.btn_ask_text = ttk.Button(
            main, text="❓ Nur Frage", command=self.on_ask_text
        )
        self.btn_ask_text.grid(row=2, column=1, sticky="w", pady=6, padx=(6, 0))

        self.btn_clean_shots = ttk.Button(
            main, text="🧹 Screenshots-Ordner leeren", command=self.clean_screenshots
        )
        self.btn_clean_shots.grid(row=2, column=2, sticky="w", pady=6, padx=(6, 0))

        self.btn_quit = ttk.Button(
            main, text="Beenden", command=self.root.quit
        )
        self.btn_quit.grid(row=2, column=3, sticky="e", pady=6)

        self.entry.bind("<Control-Return>", self._on_ctrl_enter)

    def append_chat(self, who: str, text: str):
        self.chat.configure(state="normal")
        self.chat.insert("end", f"{who}: {text}\n\n")
        self.chat.configure(state="disabled")
        self.chat.see("end")

    def _on_ctrl_enter(self, event):
        self.on_ask_screen()
        return "break"

    # ---- Aktionen ----

    def on_ask_screen(self):
        question = self.entry.get("1.0", "end").strip()
        if not question:
            self.append_chat("SYSTEM", "Bitte erst eine Frage eingeben.")
            return

        self.append_chat("DU", question)
        self.entry.delete("1.0", "end")

        self.btn_ask_screen.configure(state="disabled")
        self.btn_ask_text.configure(state="disabled")
        self.append_chat("SYSTEM", "Ich analysiere deinen Bildschirm...")

        threading.Thread(
            target=self._worker_ask_screen,
            args=(question,),
            daemon=True,
        ).start()

    def _worker_ask_screen(self, question: str):
        try:
            shots = capture_all_screens()
            if not shots:
                answer = "Ich konnte keinen Bildschirm aufnehmen."
            else:
                # nur Monitor 1 für KI nehmen (kostet Tokens!)
                _, img = shots[0]
                answer = ask_vision(question, img)
        except Exception as e:
            answer = f"Fehler bei der Analyse: {e}"

        self.root.after(0, self._finish_answer, answer)

    def on_ask_text(self):
        question = self.entry.get("1.0", "end").strip()
        if not question:
            self.append_chat("SYSTEM", "Bitte erst eine Frage eingeben.")
            return

        self.append_chat("DU", question)
        self.entry.delete("1.0", "end")

        self.btn_ask_screen.configure(state="disabled")
        self.btn_ask_text.configure(state="disabled")
        self.append_chat("SYSTEM", "Ich denke nach...")

        threading.Thread(
            target=self._worker_ask_text,
            args=(question,),
            daemon=True,
        ).start()

    def _worker_ask_text(self, question: str):
        try:
            answer = ask_text_only(question)
        except Exception as e:
            answer = f"Fehler bei der Anfrage: {e}"
        self.root.after(0, self._finish_answer, answer)

    def _finish_answer(self, answer: str):
        self.append_chat("KI", answer)
        speak(answer)
        self.btn_ask_screen.configure(state="normal")
        self.btn_ask_text.configure(state="normal")

    def clean_screenshots(self):
        count = 0
        for name in os.listdir(SCREENSHOT_DIR):
            path = os.path.join(SCREENSHOT_DIR, name)
            if os.path.isfile(path):
                try:
                    os.remove(path)
                    count += 1
                except Exception:
                    pass
        self.append_chat("SYSTEM", f"Screenshots-Ordner aufgeräumt ({count} Dateien gelöscht).")
        log_line(f"Screenshots gelöscht: {count}")

    # ---- Auto-Loop (nur Screenshots + Log, keine KI, um Kosten zu sparen) ----

    def auto_loop(self):
        try:
            shots = capture_all_screens()
            if shots:
                self.append_chat(
                    "SYSTEM",
                    f"Auto-Screenshot gespeichert ({len(shots)} Monitor(e))."
                )
                log_line(f"Auto-Screenshots: {len(shots)} Monitore.")
        except Exception as e:
            log_line(f"Fehler bei Auto-Screenshot: {e}")

        # nächsten Lauf planen
        self.root.after(AUTO_INTERVAL_MS, self.auto_loop)


def main():
    root = tk.Tk()
    app = KIKumpelApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
