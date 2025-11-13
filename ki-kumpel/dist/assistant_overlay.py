import tkinter as tk
import time
import threading

# ---------------------------------------------------------
# 💠 OVERLAY-FENSTER (A5 Neon-Tech Stil)
# ---------------------------------------------------------
class AssistantOverlay:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("AI Assistant Overlay")

        # Fenster-Eigenschaften
        self.root.geometry("300x150")
        self.root.overrideredirect(True)  
        self.root.attributes("-topmost", True)  
        self.root.attributes("-alpha", 0.88)

        # Position rechts unten
        self.set_bottom_right()

        # Canvas für Neon-Design
        self.canvas = tk.Canvas(self.root, width=300, height=150,
                                bg="#0a0f1a", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        # Neon-Rahmen Animation
        self.neon_color_index = 0
        self.neon_colors = ["#1c77c3", "#1593e8", "#32afff", "#1593e8"]
        self.draw_neon_border()

        # Textfeld
        self.text_id = self.canvas.create_text(
            10, 10,
            anchor="nw",
            text="KI-Kumpel aktiv...",
            fill="#dbeafe",
            font=("Segoe UI", 11),
            width=280
        )

        # Animation starten
        self.animate_border()

    # ---------------------------------------------------------
    # Fenster rechts unten positionieren
    # ---------------------------------------------------------
    def set_bottom_right(self):
        self.root.update_idletasks()
        w = 300
        h = 150

        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()

        x = screen_w - w - 20
        y = screen_h - h - 40

        self.root.geometry(f"{w}x{h}+{x}+{y}")

    # ---------------------------------------------------------
    # Neon-Rahmen zeichnen
    # ---------------------------------------------------------
    def draw_neon_border(self):
        color = self.neon_colors[self.neon_color_index]
        self.canvas.delete("border")

        self.canvas.create_rectangle(
            2, 2, 298, 148,
            outline=color,
            width=3,
            tag="border"
        )

    # ---------------------------------------------------------
    # Animation
    # ---------------------------------------------------------
    def animate_border(self):
        self.neon_color_index = (self.neon_color_index + 1) % len(self.neon_colors)
        self.draw_neon_border()
        self.root.after(500, self.animate_border)

    # ---------------------------------------------------------
    # Text setzen
    # ---------------------------------------------------------
    def update_text(self, text):
        self.canvas.itemconfig(self.text_id, text=text)

    # ---------------------------------------------------------
    # Mainloop starten
    # ---------------------------------------------------------
    def run(self):
        self.root.mainloop()


# ---------------------------------------------------------
# ▶️ START
# ---------------------------------------------------------
if __name__ == "__main__":
    overlay = AssistantOverlay()

    def demo_loop():
        demo_messages = [
            "KI-Kumpel aktiv...",
            "Monitore erkannt...",
            "Screenshot wird analysiert...",
            "Outlook erkannt...",
            "TechDirect erkannt...",
            "Warte auf nächste Aktion..."
        ]
        while True:
            for msg in demo_messages:
                overlay.update_text(msg)
                time.sleep(2)

    # Demo läuft im Background (darf kein Tkinter benutzen → OK)
    threading.Thread(target=demo_loop, daemon=True).start()

    # Tkinter muss im Hauptthread laufen
    overlay.run()
