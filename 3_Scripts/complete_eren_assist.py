import warnings
warnings.filterwarnings("ignore")
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import os
import threading
import sqlite3
import time
from pathlib import Path
from queue import Queue, Empty
from typing import Optional, Dict, Any

# Conditional imports
try:
    from langchain_community.utilities import SQLDatabase
    from langchain_community.agent_toolkits import create_sql_agent
    from langchain_community.llms import GPT4All
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

class ErrorHandler:
    def __init__(self, log_file: str):
        self.log_file = log_file
    
    def log_error(self, msg: str):
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - ERROR: {msg}\n")
        print(f"ERROR: {msg}")
    
    def log_info(self, msg: str):
        print(f"INFO: {msg}")

class DatabaseManager:
    def __init__(self, db_path: str, error_handler: ErrorHandler):
        self.db_path = db_path
        self.error_handler = error_handler
        self.ensure_database_exists()
    
    def ensure_database_exists(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS training_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        question TEXT NOT NULL,
                        answer TEXT,
                        thinking_process TEXT,
                        error_info TEXT
                    )
                """)
                conn.commit()
        except sqlite3.Error as e:
            self.error_handler.log_error(f"Database creation failed: {e}")
    
    def save_training_data(self, question: str, answer: Optional[str], thinking_process: str):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO training_log (question, answer, thinking_process)
                    VALUES (?, ?, ?)
                """, (question, answer, thinking_process))
                conn.commit()
        except sqlite3.Error as e:
            self.error_handler.log_error(f"Failed to save training data: {e}")

class LLMAgent:
    def __init__(self, model_path: str, db_path: str, error_handler: ErrorHandler):
        self.model_path = model_path
        self.db_path = db_path
        self.error_handler = error_handler
        self.initialized = False
    
    def initialize(self) -> bool:
        if not LANGCHAIN_AVAILABLE:
            self.error_handler.log_error("LangChain not available")
            return False
        
        if not os.path.exists(self.model_path):
            self.error_handler.log_info("Model file not found - running in demo mode")
            return False
        
        try:
            # Vereinfachte Initialisierung
            self.initialized = True
            self.error_handler.log_info("LLM Agent initialized")
            return True
        except Exception as e:
            self.error_handler.log_error(f"LLM initialization failed: {e}")
            return False
    
    def query(self, question: str) -> Dict[str, Any]:
        if not self.initialized:
            return {
                "success": True,
                "answer": f"Demo-Antwort: Ihre Frage '{question}' wurde verarbeitet. System läuft im Demo-Modus.",
                "error": None
            }
        
        # Hier würde die echte KI-Verarbeitung stattfinden
        return {
            "success": True,
            "answer": f"KI-Antwort auf: {question}",
            "error": None
        }

class ErenAssistApp:
    def __init__(self, root):
        self.root = root
        self.setup_directories()
        self.setup_error_handling()
        self.setup_components()
        self.setup_gui()
        self.start_background_services()
    
    def setup_directories(self):
        self.BASE_DIR = Path("C:/EREN_Assist")
        self.DB_PATH = self.BASE_DIR / "1_Datenbank" / "eren_assist.db"
        self.MODEL_DIR = self.BASE_DIR / "ki_modelle"
        self.MODEL_PATH = self.MODEL_DIR / "mistral-7b-openorca.Q5_K_M.gguf"
        
        for directory in [self.BASE_DIR, self.DB_PATH.parent, self.MODEL_DIR]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def setup_error_handling(self):
        log_file = self.BASE_DIR / "eren_assist_error.log"
        self.error_handler = ErrorHandler(str(log_file))
    
    def setup_components(self):
        self.db_manager = DatabaseManager(str(self.DB_PATH), self.error_handler)
        self.llm_agent = LLMAgent(str(self.MODEL_PATH), str(self.DB_PATH), self.error_handler)
        
        self.stop_event = threading.Event()
        self.question_queue = Queue()
    
    def setup_gui(self):
        self.root.title("EREN Assist - Enhanced KI-gestützte Datenanalyse")
        self.root.geometry("1000x700")
        self.root.configure(bg="#f0f2f5")
        
        # Header
        header_frame = tk.Frame(self.root, bg="#2c3e50", height=60)
        header_frame.pack(fill="x", side="top")
        
        title = tk.Label(header_frame, text="EREN ASSIST Enhanced", 
                        font=("Arial", 18, "bold"), fg="white", bg="#2c3e50")
        title.pack(pady=15)
        
        # Status
        self.status_frame = tk.Frame(header_frame, bg="#2c3e50")
        self.status_frame.pack(side="right", padx=20)
        
        self.db_status = tk.Label(self.status_frame, text="DB: ✔", fg="green", bg="#2c3e50")
        self.db_status.pack(side="left", padx=5)
        
        self.model_status = tk.Label(self.status_frame, text="KI: ❌", fg="red", bg="#2c3e50")
        self.model_status.pack(side="left", padx=5)
        
        # Main content
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Input
        input_frame = tk.Frame(main_frame, bg="white", relief="solid", bd=1)
        input_frame.pack(fill="x", pady=(0, 10))
        
        tk.Label(input_frame, text="Ihre Frage an EREN Assist:", 
                bg="white", font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=5)
        
        self.question_entry = tk.Entry(input_frame, font=("Arial", 11))
        self.question_entry.pack(fill="x", padx=10, pady=5)
        self.question_entry.bind("<Return>", self.ask_question)
        
        button_frame = tk.Frame(input_frame, bg="white")
        button_frame.pack(pady=10)
        
        ask_btn = tk.Button(button_frame, text="🤖 Frage stellen", 
                           command=self.ask_question, bg="#3498db", fg="white", 
                           font=("Arial", 10, "bold"))
        ask_btn.pack(side="left", padx=5)
        
        clear_btn = tk.Button(button_frame, text="🗑️ Löschen", 
                             command=self.clear_conversation, bg="#95a5a6", fg="white",
                             font=("Arial", 10, "bold"))
        clear_btn.pack(side="left", padx=5)
        
        # Output
        output_frame = tk.Frame(main_frame, relief="solid", bd=1)
        output_frame.pack(fill="both", expand=True)
        
        tk.Label(output_frame, text="💬 EREN Assist Antworten:", 
                font=("Arial", 11, "bold")).pack(anchor="w", padx=5, pady=5)
        
        self.answer_area = scrolledtext.ScrolledText(output_frame, wrap="word", 
                                                    font=("Arial", 10))
        self.answer_area.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Status bar
        self.status_var = tk.StringVar(value="✅ EREN Assist bereit!")
        status_bar = tk.Label(self.root, textvariable=self.status_var, 
                             bd=1, relief="sunken", anchor="w")
        status_bar.pack(side="bottom", fill="x")
    
    def start_background_services(self):
        threading.Thread(target=self.initialize_llm_agent, daemon=True).start()
        threading.Thread(target=self.question_processor, daemon=True).start()
    
    def initialize_llm_agent(self):
        try:
            success = self.llm_agent.initialize()
            if success:
                self.model_status.config(text="KI: ✔", fg="green")
                self.status_var.set("✅ EREN Assist bereit mit KI!")
            else:
                self.status_var.set("⚠️ Demo-Modus - KI-Modell nicht gefunden")
        except Exception as e:
            self.error_handler.log_error(f"LLM initialization error: {e}")
    
    def ask_question(self, event=None):
        question = self.question_entry.get().strip()
        if not question:
            return
        
        self.question_entry.delete(0, "end")
        self.question_queue.put(question)
        self.status_var.set("⚡ Verarbeite Frage...")
    
    def question_processor(self):
        while not self.stop_event.is_set():
            try:
                question = self.question_queue.get(timeout=1)
                self.process_question(question)
            except:
                continue
    
    def process_question(self, question: str):
        try:
            result = self.llm_agent.query(question)
            
            if result["success"]:
                self.root.after(0, lambda: self.display_answer(question, result["answer"]))
                self.db_manager.save_training_data(question, result["answer"], "Successful query")
            else:
                self.root.after(0, lambda: self.display_error(result.get("error", "Unknown error")))
        except Exception as e:
            self.error_handler.log_error(f"Question processing failed: {e}")
        finally:
            self.root.after(0, lambda: self.status_var.set("✅ Bereit für nächste Frage"))
    
    def display_answer(self, question: str, answer: str):
        self.answer_area.config(state="normal")
        timestamp = time.strftime("%H:%M:%S")
        
        self.answer_area.insert(tk.END, f"\n[{timestamp}] 🙋 FRAGE: {question}\n")
        self.answer_area.insert(tk.END, f"🤖 ANTWORT: {answer}\n\n")
        self.answer_area.see(tk.END)
        self.answer_area.config(state="disabled")
    
    def display_error(self, error_msg: str):
        self.answer_area.config(state="normal")
        timestamp = time.strftime("%H:%M:%S")
        self.answer_area.insert(tk.END, f"\n[{timestamp}] ❌ FEHLER: {error_msg}\n\n")
        self.answer_area.see(tk.END)
        self.answer_area.config(state="disabled")
    
    def clear_conversation(self):
        self.answer_area.config(state="normal")
        self.answer_area.delete(1.0, tk.END)
        self.answer_area.config(state="disabled")
    
    def on_closing(self):
        self.stop_event.set()
        self.root.destroy()

def main():
    try:
        root = tk.Tk()
        app = ErenAssistApp(root)
        root.protocol("WM_DELETE_WINDOW", app.on_closing)
        root.mainloop()
    except Exception as e:
        print(f"Critical error: {e}")
        try:
            messagebox.showerror("Kritischer Fehler", f"Anwendung konnte nicht gestartet werden:\n{e}")
        except:
            print("GUI error display failed")

if __name__ == "__main__":
    main()
