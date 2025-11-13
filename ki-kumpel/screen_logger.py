import os
import time
import base64
import mss
from PIL import Image
from openai import OpenAI

# ----------------------------------------------------------------------
# 🔧 CLIENT INITIALISIEREN (benutzt deinen OPENAI_API_KEY aus System-Umgebung)
# ----------------------------------------------------------------------
client = OpenAI()

# ----------------------------------------------------------------------
# 🖼️ FUNKTION: Screenshot über ALLE MONITORE (Monitor 0 = kompletter Desktop)
# ----------------------------------------------------------------------
def capture_full_desktop(filepath="screenshot.png"):
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

    response = client.responses.create(
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
