import threading
import tkinter as tk

class OverlayWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.geometry("450x300+50+50")
        self.root.title("KI-Kumpel Overlay")
        self.root.configure(bg="#1e1e1e")

        self.text = tk.Text(self.root, bg="#1e1e1e", fg="white", wrap="word")
        self.text.pack(expand=True, fill="both")

        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        self.root.mainloop()

    def show(self, message):
        self.text.delete(1.0, tk.END)
        self.text.insert(tk.END, message)
        self.root.lift()
        self.root.focus_force()
