import pystray
from pystray import MenuItem as item
from PIL import Image
import sys, os
import tkinter as tk
from tkinter import simpledialog, messagebox
import mss

def resource_path(relative):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative)
    return os.path.join(os.path.abspath("."), relative)

def take_screenshot():
    try:
        with mss.mss() as sct:
            filename = "screenshot.png"
            sct.shot(output=filename)
            messagebox.showinfo("Screenshot", f"Screenshot gespeichert: {filename}")
    except Exception as e:
        messagebox.showerror("Screenshot Fehler", str(e))

def ask_text():
    root = tk.Tk()
    root.withdraw()
    text = simpledialog.askstring("KI-Kumpel", "Text eingeben:")
    if text:
        messagebox.showinfo("Text erhalten", f"Du hast eingegeben: {text}")

def on_quit(icon, item):
    icon.stop()

def create_tray():
    icon_path = resource_path("src/assets/ChatGPT.ico")  # <--- WICHTIG
    print("Lade Icon:", icon_path)

    try:
        icon_image = Image.open(icon_path)
    except Exception as e:
        print("Fehler beim Laden des Icons:", e)
        sys.exit(1)

    menu = (
        item("Screenshot an KI senden", lambda : take_screenshot()),
        item("Text an KI senden", lambda : ask_text()),
        item("Beenden", on_quit)
    )

    icon = pystray.Icon("KI-Kumpel", icon_image, "KI-Kumpel", menu)
    print("Starte Tray...")
    icon.run()

if __name__ == "__main__":
    print("KI-Kumpel startet...")
    create_tray()
