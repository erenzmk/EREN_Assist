import os
import time
import base64
from typing import List, Tuple

from dependency_utils import resolve_dependencies, format_dependency_list

# ----------------------------------------------------------------------
# 🔧 Abhängigkeiten prüfen
# ----------------------------------------------------------------------
REQUIRED_DEPENDENCIES: List[Tuple[str, str]] = [
    ("mss", "mss"),
    ("PIL.Image", "Pillow"),
    ("openai", "openai>=1.0.0"),
]

_MODULES, MISSING_REQUIRED, _MISSING_OPTIONAL = resolve_dependencies(REQUIRED_DEPENDENCIES)

mss = _MODULES.get("mss")
Image = _MODULES.get("PIL.Image")
_openai_module = _MODULES.get("openai")

if _openai_module and hasattr(_openai_module, "OpenAI"):
    OpenAI = _openai_module.OpenAI
else:
    OpenAI = None
    if _openai_module is not None:
        MISSING_REQUIRED.append(("openai.OpenAI", "openai>=1.0.0"))

client = None


def ensure_dependencies() -> bool:
    if MISSING_REQUIRED:
        print("Fehlende Python-Pakete: " + format_dependency_list(MISSING_REQUIRED))
        pip_args = " ".join(dict.fromkeys(pip for _, pip in MISSING_REQUIRED))
        print("Bitte installiere sie mit: pip install " + pip_args)
        return False
    return True


def get_client():
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

# ----------------------------------------------------------------------
# 🖼️ FUNKTION: Screenshot über ALLE MONITORE (Monitor 0 = kompletter Desktop)
# ----------------------------------------------------------------------
def capture_full_desktop(filepath="screenshot.png"):
    if mss is None or Image is None:
        raise RuntimeError("Screenshot-Funktion erfordert die Pakete mss und Pillow.")

    with mss.mss() as sct:
        monitor = sct.monitors[0]  # 0 = ALL MONITORS zusammen
        screenshot = sct.grab(monitor)

        img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
        img.save(filepath)

        return filepath

# ----------------------------------------------------------------------
# 🧠 FUNKTION: Screenshot an KI schicken + Beschreibung erhalten
# ----------------------------------------------------------------------
def describe_screenshot(image_path):
    with open(image_path, "rb") as f:
        img_bytes = f.read()

    img_b64 = base64.b64encode(img_bytes).decode("utf-8")

    print("➡️ Sende Screenshot an KI...")

    client_instance = get_client()

    response = client_instance.responses.create(
        model="gpt-4.1-mini",
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": "Beschreibe genau, was auf meinem Bildschirm zu sehen ist. Wenn du Tools wie Outlook, TechDirect, DFSM, LSTC oder Browserfenster erkennst, sag es explizit."
                    },
                    {
                        "type": "input_image",
                        "image_url": f"data:image/png;base64,{img_b64}"
                    }
                ]
            }
        ]
    )

    return response.output_text

# ----------------------------------------------------------------------
# 📝 FUNKTION: Ergebnis in Datei speichern
# ----------------------------------------------------------------------
def log_result(text):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    entry = f"{timestamp}\n{text}\n\n"

    with open("ki_log.txt", "a", encoding="utf-8") as f:
        f.write(entry)

    print("✔️ Eintrag gespeichert.")

# ----------------------------------------------------------------------
# 🔁 ENDLOSSCHLEIFE: Alle X Sekunden Screenshot + Analyse
# ----------------------------------------------------------------------
def loop_logger(interval_seconds=120):
    if not ensure_dependencies():
        return

    if not os.getenv("OPENAI_API_KEY"):
        print("OPENAI_API_KEY ist nicht gesetzt. Bitte exportieren oder in den Umgebungsvariablen hinterlegen.")
        return

    while True:
        print("➡️ Mache Screenshot über alle Monitore...")
        img_path = capture_full_desktop()

        print("➡️ Sende an KI...")
        desc = describe_screenshot(img_path)

        log_result(desc)

        print(f"Warte {interval_seconds} Sekunden...\n")
        time.sleep(interval_seconds)

# ----------------------------------------------------------------------
# ▶️ PROGRAMM START
# ----------------------------------------------------------------------
if __name__ == "__main__":
    loop_logger(interval_seconds=120)  # alle 2 Minuten
