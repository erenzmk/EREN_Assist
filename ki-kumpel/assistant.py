import os
import time
import threading
import base64
from datetime import datetime
from queue import Queue, Empty
from typing import List, Optional, Tuple

import tkinter as tk
from tkinter import scrolledtext

from dependency_utils import resolve_dependencies, format_dependency_list

# =========================
#  KONFIGURATION
# =========================

# Intervall in Sekunden (z. B. 120 = alle 2 Minuten)
CAPTURE_INTERVAL = 120

# Logfile für Text
LOG_FILE = "activity_log.txt"

# Abhängigkeitsprüfung
REQUIRED_DEPENDENCIES: List[Tuple[str, str]] = [
    ("mss", "mss"),
    ("PIL.Image", "Pillow"),
    ("openai", "openai>=1.0.0"),
]

OPTIONAL_DEPENDENCIES: List[Tuple[str, str]] = [
    ("pyttsx3", "pyttsx3"),
]

_MODULES, MISSING_REQUIRED, MISSING_OPTIONAL = resolve_dependencies(
    REQUIRED_DEPENDENCIES,
    OPTIONAL_DEPENDENCIES,
)

mss = _MODULES.get("mss")
Image = _MODULES.get("PIL.Image")
_openai_module = _MODULES.get("openai")

if _openai_module and hasattr(_openai_module, "OpenAI"):
    OpenAI = _openai_module.OpenAI
else:
    OpenAI = None
    if _openai_module is not None:
        MISSING_REQUIRED.append(("openai.OpenAI", "openai>=1.0.0"))

pyttsx3 = _MODULES.get("pyttsx3")

client: Optional[object] = None


def ensure_dependencies() -> bool:
    """Prüft, ob alle Pflicht-Abhängigkeiten vorhanden sind."""
    if MISSING_REQUIRED:
        print("Fehlende Python-Pakete: " + format_dependency_list(MISSING_REQUIRED))
        pip_args = " ".join(dict.fromkeys(pip for _, pip in MISSING_REQUIRED))
        print("Bitte installiere sie mit: pip install " + pip_args)
        print("Alternativ kannst du auch alle Pakete über 'pip install -r requirements.txt' installieren.")
        print("(PowerShell) .\\.venv\\Scripts\\Activate.ps1  ->  pip install -r requirements.txt")
        return False

    if MISSING_OPTIONAL:
        print("Hinweis: optionale Pakete fehlen → " +
              format_dependency_list(MISSING_OPTIONAL))
        print("Die Anwendung läuft trotzdem, aber bestimmte Komfort-Funktionen sind deaktiviert.")

    return True


def get_client():
    """Erstellt bei Bedarf den OpenAI-Client."""
    global client
    if client is not None:
        return client

    if OpenAI is None:
        raise RuntimeError("OpenAI SDK ist nicht verfügbar.")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY ist nicht gesetzt.")

    client = OpenAI(api_key=api_key)
    return client

# =========================
#  SCREENSHOT & KI-ANALYSE
# =========================

def take_screenshot(filename="screen.png"):
    if mss is None or Image is None:
        raise RuntimeError("Screenshot-Funktion erfordert die Pakete mss und Pillow.")

    with mss.mss() as sct:
        monitor = sct.monitors[1]  # Hauptmonitor
        sct_img = sct.grab(monitor)
        img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
        img.save(filename)
    return filename

def describe_screenshot(image_path):
    # Bild in Base64 umwandeln
    with open(image_path, "rb") as f:
        image_bytes = f.read()
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")

    try:
        client_instance = get_client()
        response = client_instance.responses.create(
            model="gpt-4.1-mini",
            input=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": (
                                "Du bist ein Assistent, der den Bildschirm eines Dispatchers beobachtet. "
                                "Beschreibe kurz und klar, was gerade passiert:\n"
                                "- Welche Programme / Fenster sind sichtbar?\n"
                                "- Was scheint die aktuelle Aufgabe zu sein?\n"
                                "- Gibt es Fehlermeldungen oder wichtige Hinweise?\n"
                                "Antworte maximal in 5 Sätzen auf Deutsch."
                            ),
                        },
                        {
                            "type": "input_image",
                            "image_url": f"data:image/png;base64,{image_b64}",
                        },
                    ],
                }
            ],
        )

        text = response.output[0].content[0].text
        return text.strip()
    except Exception as e:
        return f"[KI-Fehler] {e}"

# =========================
#  TRIGGER-ERKENNUNG
# =========================

def detect_triggers(description: str):
    """
    Simple Keyword-Erkennung, kann später ausgebaut werden.
    Gibt eine kurze Status-Zeile zurück.
    """
    desc_lower = description.lower()
    tags = []

    # Outlook / Mail
    if "outlook" in desc_lower or "e-mail" in desc_lower or "email" in desc_lower:
        tags.append("📨 Outlook / Mail erkannt")

    # Dell / DFSM / TechDirect
    if "dfsm" in desc_lower or "techdirect" in desc_lower or "dell" in desc_lower:
        tags.append("💻 Dell / DFSM / TechDirect")

    # Lenovo / LSTC / Golden Key
    if "lenovo" in desc_lower or "golden key" in desc_lower or "lstc" in desc_lower:
        tags.append("💼 Lenovo / GoldenKey / LSTC")

    # Fehler / Warnung
    if "fehler" in desc_lower or "error" in desc_lower or "warnung" in desc_lower:
        tags.append("⚠️ Fehler/Warnung erkannt")

    # Browser / viele Tabs
    if "chrome" in desc_lower or "edge" in desc_lower or "firefox" in desc_lower or "browser" in desc_lower:
        tags.append("🌐 Browser-Aktivität")

    if not tags:
        return "🔍 Keine speziellen Muster erkannt"
    else:
        return " | ".join(tags)

# =========================
#  TEXT-TO-SPEECH
# =========================

class Speaker:
    def __init__(self):
        self.available = pyttsx3 is not None

        if self.available:
            self.engine = pyttsx3.init()
            # Stimme etwas anpassen
            voices = self.engine.getProperty("voices")
            if voices:
                # Nimm die erste verfügbare Stimme
                self.engine.setProperty("voice", voices[0].id)
            self.engine.setProperty("rate", 190)  # Sprechgeschwindigkeit
            self.engine.setProperty("volume", 0.9)

            self.queue = Queue()
            self.thread = threading.Thread(target=self._run, daemon=True)
            self.thread.start()
        else:
            self.engine = None
            self.queue = None
            self.thread = None

    def _run(self):
        if not self.available or self.queue is None:
            return

        while True:
            try:
                text = self.queue.get(timeout=0.1)
            except Empty:
                continue
            try:
                self.engine.say(text)
                self.engine.runAndWait()
            except Exception:
                # TTS-Fehler ignorieren, damit der Bot weiterläuft
                pass

    def say(self, text: str):
        # Nur kurze Hinweise sprechen, nicht ganze Romane
        if not text:
            return
        if not self.available or self.queue is None:
            return
        self.queue.put(text)

# =========================
#  GUI (NEON-OVERLAY)
# =========================

class OverlayApp:
    def __init__(self, root, speaker: Speaker):
        self.root = root
        self.speaker = speaker

        self.root.title("KI-Kumpel")
        self.root.attributes("-topmost", True)
        self.root.geometry("420x320+20+20")  # kleines Fenster links oben
        self.root.configure(bg="#050816")   # sehr dunkles Blau/Lila

        # Neon-Rahmen
        self.frame = tk.Frame(self.root, bg="#050816", highlightthickness=2, highlightbackground="#00f3ff")
        self.frame.pack(fill="both", expand=True, padx=6, pady=6)

        # Titel
        self.title_label = tk.Label(
            self.frame,
            text="🧠 KI-Kumpel – Live Monitor",
            fg="#00f3ff",
            bg="#050816",
            font=("Segoe UI", 11, "bold")
        )
        self.title_label.pack(pady=(4, 2))

        # Statuszeile (Triggers)
        self.status_label = tk.Label(
            self.frame,
            text="Status: wartet...",
            fg="#f472ff",
            bg="#050816",
            font=("Segoe UI", 9, "bold"),
            wraplength=380,
            justify="left"
        )
        self.status_label.pack(pady=(0, 4))

        # Scroll-Text für letzte Beschreibung
        self.text_area = scrolledtext.ScrolledText(
            self.frame,
            width=50,
            height=10,
            bg="#020617",
            fg="#e5e7eb",
            insertbackground="#00f3ff",
            font=("Consolas", 9),
            relief="flat",
            wrap="word"
        )
        self.text_area.pack(fill="both", expand=True, padx=6, pady=(0, 4))
        self.text_area.insert("end", "Letzte KI-Beschreibung erscheint hier...\n")
        self.text_area.config(state="disabled")

        # Button-Leiste
        btn_frame = tk.Frame(self.frame, bg="#050816")
        btn_frame.pack(fill="x", pady=(4, 4))

        self.btn_summary = tk.Button(
            btn_frame,
            text="📝 Tag zusammenfassen",
            command=self.request_summary,
            bg="#0f172a",
            fg="#e5e7eb",
            activebackground="#1e293b",
            activeforeground="#ffffff",
            relief="flat",
            font=("Segoe UI", 9, "bold"),
            padx=6,
            pady=3
        )
        self.btn_summary.pack(side="left", padx=(4, 2))

        self.btn_quit = tk.Button(
            btn_frame,
            text="✖ Beenden",
            command=self.root.quit,
            bg="#7f1d1d",
            fg="#fee2e2",
            activebackground="#b91c1c",
            activeforeground="#ffffff",
            relief="flat",
            font=("Segoe UI", 9, "bold"),
            padx=6,
            pady=3
        )
        self.btn_quit.pack(side="right", padx=(2, 4))

        # Queue für Hintergrund-Thread → GUI
        self.update_queue = Queue()

        # Polling für GUI-Updates
        self.root.after(200, self.process_queue)

    def process_queue(self):
        """Verarbeitet Nachrichten aus dem Worker-Thread."""
        try:
            while True:
                item = self.update_queue.get_nowait()
                kind = item.get("type")
                if kind == "description":
                    self._update_description(item["text"])
                elif kind == "status":
                    self._update_status(item["text"])
                elif kind == "speak":
                    self.speaker.say(item["text"])
        except Empty:
            pass

        self.root.after(200, self.process_queue)

    def _update_description(self, text):
        self.text_area.config(state="normal")
        self.text_area.delete("1.0", "end")
        self.text_area.insert("end", text + "\n")
        self.text_area.config(state="disabled")

    def _update_status(self, text):
        self.status_label.config(text=text)

    def request_summary(self):
        """Knopf: Tageszusammenfassung anfordern (aus Logfile)."""
        try:
            if not os.path.exists(LOG_FILE):
                self._update_description("Noch kein Logfile vorhanden.")
                return

            with open(LOG_FILE, "r", encoding="utf-8") as f:
                content = f.read()

            if not content.strip():
                self._update_description("Logfile ist leer.")
                return

            summary = create_summary(content)
            self._update_description(summary)
            self.speaker.say("Zusammenfassung deines Tages wurde erstellt.")
        except Exception as e:
            self._update_description(f"[Fehler bei Zusammenfassung] {e}")

# =========================
#  TAGESZUSAMMENFASSUNG
# =========================

def create_summary(log_text: str) -> str:
    """Fragt die KI nach einer kompakten Tageszusammenfassung."""
    try:
        client_instance = get_client()
        response = client_instance.responses.create(
            model="gpt-4.1-mini",
            input=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": (
                                "Du erhältst ein Log mit zeitlichen Einträgen zu Bildschirmaktivitäten eines Dispatchers. "
                                "Erstelle eine strukturierte, kurze Zusammenfassung des Tages:\n"
                                "- Stichpunkte zu den wichtigsten Tätigkeiten\n"
                                "- Auffällige Probleme / Fehler\n"
                                "- Besondere Kunden/Orte, falls erkennbar\n\n"
                                "Log:\n" + log_text
                            ),
                        }
                    ],
                }
            ],
        )
        return response.output[0].content[0].text.strip()
    except Exception as e:
        return f"[KI-Fehler bei Zusammenfassung] {e}"

# =========================
#  BACKGROUND-LOOP
# =========================

def worker_loop(app: OverlayApp):
    """Läuft im Hintergrund-Thread, macht Screenshots und KI-Analyse."""
    while True:
        try:
            app.update_queue.put({"type": "status", "text": "📸 Screenshot wird erstellt..."})
            img_path = take_screenshot()

            app.update_queue.put({"type": "status", "text": "🤖 Sende an KI..."})
            description = describe_screenshot(img_path)

            triggers = detect_triggers(description)

            # Log schreiben
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            entry = f"[{timestamp}]\n{description}\n-- {triggers}\n" + "-" * 60 + "\n"

            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(entry)

            # GUI updaten
            app.update_queue.put({"type": "description", "text": f"{timestamp}\n{description}"})
            app.update_queue.put({"type": "status", "text": f"✅ {triggers}"})

            # Bei bestimmten Triggern was sagen
            if "Fehler" in triggers or "Warnung" in triggers:
                app.update_queue.put({
                    "type": "speak",
                    "text": "Achtung, ich sehe eine Fehlermeldung auf deinem Bildschirm."
                })

            time.sleep(CAPTURE_INTERVAL)
        except Exception as e:
            app.update_queue.put({"type": "status", "text": f"[Worker-Fehler] {e}"})
            time.sleep(CAPTURE_INTERVAL)

# =========================
#  MAIN
# =========================

def main():
    if not ensure_dependencies():
        return

    # Kleiner Check für API-Key
    if not os.getenv("OPENAI_API_KEY"):
        print("OPENAI_API_KEY ist nicht gesetzt. Bitte zuerst setzen:")
        print('$env:OPENAI_API_KEY="DEIN_KEY_HIER"  (PowerShell)')
        print('export OPENAI_API_KEY="DEIN_KEY_HIER"  (Linux/macOS)')
        return

    speaker = Speaker()

    root = tk.Tk()
    app = OverlayApp(root, speaker)

    # Hintergrund-Thread starten
    t = threading.Thread(target=worker_loop, args=(app,), daemon=True)
    t.start()

    root.mainloop()

if __name__ == "__main__":
    main()
