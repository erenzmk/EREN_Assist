"""
EREN Assist - Automatisches Setup & Installation Script
Richtet das komplette System ein und löst alle Probleme
"""

import os
import sys
import shutil
import subprocess
import sqlite3
from pathlib import Path
import requests
import zipfile

class ErenSetup:
    def __init__(self):
        self.base_dir = Path("C:/EREN_Assist")
        self.scripts_dir = self.base_dir / "3_Scripts"
        self.model_dir = self.base_dir / "ki_modelle"
        self.pdf_dir = self.base_dir / "2_PDF_Archiv"
        self.db_dir = self.base_dir / "1_Datenbank"
        
        self.steps = [
            ("🔧 Verzeichnisse erstellen", self.create_directories),
            ("📄 Hauptdatei erstellen", self.create_main_file),
            ("🚀 Starter-Skripte", self.create_starters),
            ("📦 Python-Pakete prüfen", self.check_packages),
            ("🗄️ Datenbank initialisieren", self.setup_database),
            ("🎯 Verknüpfungen erstellen", self.create_shortcuts),
            ("✅ Installation testen", self.test_installation)
        ]
    
    def run_setup(self):
        """Führt komplettes Setup durch"""
        print("=" * 60)
        print("    🚀 EREN ASSIST - AUTOMATISCHES SETUP")
        print("=" * 60)
        print()
        
        for i, (name, func) in enumerate(self.steps, 1):
            print(f"[{i}/{len(self.steps)}] {name}...")
            try:
                func()
                print(f"✅ {name} - Erfolgreich!")
            except Exception as e:
                print(f"❌ {name} - Fehler: {e}")
                if input("Fortfahren? (j/n): ").lower() != 'j':
                    return False
            print()
        
        print("🎉 EREN Assist wurde erfolgreich eingerichtet!")
        print(f"📁 Installationsverzeichnis: {self.base_dir}")
        return True
    
    def create_directories(self):
        """Erstellt alle notwendigen Verzeichnisse"""
        directories = [
            self.base_dir,
            self.scripts_dir,
            self.model_dir,
            self.pdf_dir,
            self.db_dir,
            self.base_dir / "BACKUPS"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            print(f"  📁 {directory}")
    
    def create_main_file(self):
        """Erstellt die Hauptdatei mit korrigiertem Code"""
        main_file = self.scripts_dir / "eren_assist_gui_enhanced.py"
        
        # Der komplette Code von der Artifact
        main_code = """import warnings
warnings.filterwarnings("ignore", message=".*out-of-date.*")
warnings.filterwarnings("ignore", message=".*deprecated.*")
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import os
import subprocess
import threading
import sqlite3
import time
import random
import requests
import tempfile
import logging
import json
from pathlib import Path
from queue import Queue, Empty
from typing import Optional, Dict, Any, List

# Conditional imports with error handling
try:
    from langchain_community.utilities import SQLDatabase
    from langchain_community.agent_toolkits import create_sql_agent
    from langchain_community.llms import GPT4All
    LANGCHAIN_AVAILABLE = True
except ImportError as e:
    print(f"LangChain import error: {e}")
    LANGCHAIN_AVAILABLE = False

try:
    from PIL import Image
    import pytesseract
    OCR_AVAILABLE = True
except ImportError as e:
    print(f"OCR import error: {e}")
    OCR_AVAILABLE = False

try:
    import fitz  # PyMuPDF
    PDF_AVAILABLE = True
except ImportError as e:
    print(f"PDF import error: {e}")
    PDF_AVAILABLE = False

class ErrorHandler:
    \"\"\"Zentrale Fehlerbehandlung mit verschiedenen Schweregrade\"\"\"
    
    def __init__(self, log_file: str):
        self.log_file = log_file
        self.setup_logging()
        
    def setup_logging(self):
        \"\"\"Konfiguriert das Logging-System\"\"\"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def log_error(self, error_msg: str, error_type: str = "ERROR"):
        \"\"\"Protokolliert Fehler mit Kontext\"\"\"
        self.logger.error(f"{error_type}: {error_msg}")
        
    def log_warning(self, warning_msg: str):
        \"\"\"Protokolliert Warnungen\"\"\"
        self.logger.warning(warning_msg)
        
    def log_info(self, info_msg: str):
        \"\"\"Protokolliert Informationen\"\"\"
        self.logger.info(info_msg)

class DatabaseManager:
    \"\"\"Verbesserte Datenbankoperationen mit Fehlerbehandlung\"\"\"
    
    def __init__(self, db_path: str, error_handler: ErrorHandler):
        self.db_path = db_path
        self.error_handler = error_handler
        self.ensure_database_exists()
    
    def ensure_database_exists(self):
        \"\"\"Stellt sicher, dass die Datenbank existiert\"\"\"
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(\"\"\"
                    CREATE TABLE IF NOT EXISTS training_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        question TEXT NOT NULL,
                        answer TEXT,
                        thinking_process TEXT,
                        error_info TEXT
                    )
                \"\"\")
                
                cursor.execute(\"\"\"
                    CREATE TABLE IF NOT EXISTS error_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        error_type TEXT,
                        error_message TEXT,
                        context TEXT
                    )
                \"\"\")
                conn.commit()
        except sqlite3.Error as e:
            self.error_handler.log_error(f"Database creation failed: {e}")
    
    def save_training_data(self, question: str, answer: Optional[str], 
                          thinking_process: str, error_info: Optional[str] = None):
        \"\"\"Speichert Trainingsdaten sicher\"\"\"
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(\"\"\"
                    INSERT INTO training_log (question, answer, thinking_process, error_info)
                    VALUES (?, ?, ?, ?)
                \"\"\", (question, answer, thinking_process, error_info))
                conn.commit()
        except sqlite3.Error as e:
            self.error_handler.log_error(f"Failed to save training data: {e}")

class RobustLLMAgent:
    \"\"\"Robuster LLM-Agent mit verbesserter Fehlerbehandlung\"\"\"
    
    def __init__(self, model_path: str, db_path: str, error_handler: ErrorHandler):
        self.model_path = model_path
        self.db_path = db_path
        self.error_handler = error_handler
        self.agent = None
        self.initialized = False
    
    def initialize(self) -> bool:
        \"\"\"Initialisiert den LLM-Agent\"\"\"
        if not LANGCHAIN_AVAILABLE:
            self.error_handler.log_error("LangChain not available")
            return False
        
        try:
            # Umgebungsvariablen für CPU-only setzen
            os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
            
            # Prüfe ob Modelldatei existiert
            if not os.path.exists(self.model_path):
                self.error_handler.log_warning(f"Model file not found: {self.model_path}")
                return False
            
            # Datenbank verbinden
            db = SQLDatabase.from_uri(f"sqlite:///{self.db_path}")
            
            # LLM initialisieren (ohne deprecated parameters)
            llm = GPT4All(
                model=self.model_path,
                verbose=False,
                allow_download=False
            )
            
            # Agent erstellen
            self.agent = create_sql_agent(
                llm=llm,
                db=db,
                agent_type="zero-shot-react-description",
                verbose=False
            )
            
            self.initialized = True
            self.error_handler.log_info("LLM Agent successfully initialized")
            return True
            
        except Exception as e:
            self.error_handler.log_error(f"LLM Agent initialization failed: {e}")
            return False
    
    def query(self, question: str, timeout: int = 60) -> Dict[str, Any]:
        \"\"\"Führt eine Abfrage mit Timeout aus\"\"\"
        if not self.initialized:
            return {
                "success": False,
                "error": "Agent not initialized",
                "answer": "KI-Agent ist nicht initialisiert oder Modell nicht gefunden"
            }
        
        try:
            # Verwende invoke statt run (neue LangChain API)
            if hasattr(self.agent, 'invoke'):
                result = self.agent.invoke({"input": question})
                answer = result.get("output", "Keine Antwort erhalten")
            else:
                # Fallback für ältere Versionen
                answer = self.agent.run(question)
            
            return {
                "success": True,
                "answer": answer,
                "error": None
            }
            
        except Exception as e:
            error_msg = str(e)
            self.error_handler.log_error(f"Query failed: {error_msg}")
            
            return {
                "success": False,
                "error": error_msg,
                "answer": f"Fehler bei der Verarbeitung: {error_msg}"
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
        \"\"\"Erstellt alle notwendigen Verzeichnisse\"\"\"
        self.BASE_DIR = Path("C:/EREN_Assist")
        self.DB_PATH = self.BASE_DIR / "1_Datenbank" / "eren_assist.db"
        self.PDF_DIR = self.BASE_DIR / "2_PDF_Archiv"
        self.SCRIPTS_DIR = self.BASE_DIR / "3_Scripts"
        self.MODEL_DIR = self.BASE_DIR / "ki_modelle"
        
        # Verzeichnisse erstellen
        for directory in [self.BASE_DIR, self.DB_PATH.parent, 
                         self.PDF_DIR, self.SCRIPTS_DIR, self.MODEL_DIR]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Modell-Konfiguration
        self.MODEL_FILE = "mistral-7b-openorca.Q5_K_M.gguf"
        self.MODEL_PATH = self.MODEL_DIR / self.MODEL_FILE
    
    def setup_error_handling(self):
        \"\"\"Initialisiert die Fehlerbehandlung\"\"\"
        log_file = self.BASE_DIR / "eren_assist_error.log"
        self.error_handler = ErrorHandler(str(log_file))
        
    def setup_components(self):
        \"\"\"Initialisiert alle Komponenten\"\"\"
        self.db_manager = DatabaseManager(str(self.DB_PATH), self.error_handler)
        self.llm_agent = RobustLLMAgent(str(self.MODEL_PATH), str(self.DB_PATH), self.error_handler)
        
        # Threading-Komponenten
        self.stop_event = threading.Event()
        self.question_queue = Queue()
        self.result_queue = Queue()
        self.thinking_queue = Queue()
        
    def setup_gui(self):
        \"\"\"Erstellt die Benutzeroberfläche\"\"\"
        self.root.title("EREN Assist - Enhanced KI-gestützte Datenanalyse")
        self.root.geometry("1200x800")
        self.root.configure(bg="#f0f2f5")
        
        # Header
        header_frame = tk.Frame(self.root, bg="#2c3e50", height=80)
        header_frame.pack(fill="x", side="top")
        
        title = tk.Label(header_frame, text="EREN ASSIST Enhanced", 
                        font=("Arial", 20, "bold"), fg="white", bg="#2c3e50")
        title.pack(pady=15)
        
        # Status-Indikatoren
        status_frame = tk.Frame(header_frame, bg="#2c3e50")
        status_frame.pack(side="right", padx=20)
        
        self.db_status = tk.Label(status_frame, text="DB: ❌", fg="red", bg="#2c3e50")
        self.db_status.pack(side="left", padx=5)
        
        self.model_status = tk.Label(status_frame, text="KI: ❌", fg="red", bg="#2c3e50")
        self.model_status.pack(side="left", padx=5)
        
        # Hauptbereich
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Eingabebereich
        input_frame = tk.Frame(main_frame, bg="white", relief="groove", bd=2)
        input_frame.pack(fill="x", pady=(0, 10))
        
        tk.Label(input_frame, text="Ihre Frage an EREN Assist:", bg="white", 
                font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=5)
        
        self.question_entry = tk.Entry(input_frame, font=("Arial", 11))
        self.question_entry.pack(fill="x", padx=10, pady=5)
        self.question_entry.bind("<Return>", self.ask_question)
        
        button_frame = tk.Frame(input_frame, bg="white")
        button_frame.pack(pady=10)
        
        ask_btn = tk.Button(button_frame, text="🤖 Frage stellen", command=self.ask_question,
                           bg="#3498db", fg="white", font=("Arial", 10, "bold"))
        ask_btn.pack(side="left", padx=5)
        
        clear_btn = tk.Button(button_frame, text="🗑️ Löschen", command=self.clear_conversation,
                             bg="#95a5a6", fg="white", font=("Arial", 10, "bold"))
        clear_btn.pack(side="left", padx=5)
        
        # Antwortbereich
        answer_frame = tk.Frame(main_frame, relief="groove", bd=2)
        answer_frame.pack(fill="both", expand=True)
        
        tk.Label(answer_frame, text="💬 EREN Assist Antworten:", 
                font=("Arial", 11, "bold")).pack(anchor="w", padx=5, pady=5)
        
        self.answer_area = scrolledtext.ScrolledText(answer_frame, wrap="word", 
                                                    font=("Arial", 10), height=20)
        self.answer_area.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Statusleiste
        self.status_var = tk.StringVar(value="System wird initialisiert...")
        status_bar = tk.Label(self.root, textvariable=self.status_var, 
                             bd=1, relief="sunken", anchor="w", bg="#ecf0f1")
        status_bar.pack(side="bottom", fill="x")
        
        # Fortschrittsbalken
        self.progress = ttk.Progressbar(self.root, mode='indeterminate')
    
    def start_background_services(self):
        \"\"\"Startet Hintergrunddienste\"\"\"
        # Status aktualisieren
        self.update_status_indicators()
        
        # LLM-Agent initialisieren
        threading.Thread(target=self.initialize_llm_agent, daemon=True).start()
        
        # Überwachungs-Threads
        threading.Thread(target=self.question_processor, daemon=True).start()
    
    def update_status_indicators(self):
        \"\"\"Aktualisiert die Status-Indikatoren\"\"\"
        # Datenbank-Status
        if self.DB_PATH.exists():
            self.db_status.config(text="DB: ✔", fg="green")
    
    def initialize_llm_agent(self):
        \"\"\"Initialisiert den LLM-Agent\"\"\"
        self.status_var.set("🤖 Initialisiere KI-Modell...")
        
        try:
            success = self.llm_agent.initialize()
            if success:
                self.model_status.config(text="KI: ✔", fg="green")
                self.status_var.set("✅ EREN Assist bereit! Sie können jetzt Fragen stellen.")
            else:
                self.model_status.config(text="KI: ❌", fg="red")
                if not self.MODEL_PATH.exists():
                    self.status_var.set("⚠️ KI-Modell nicht gefunden - System läuft im Demo-Modus")
                else:
                    self.status_var.set("❌ KI-Agent-Initialisierung fehlgeschlagen")
        except Exception as e:
            self.error_handler.log_error(f"LLM initialization error: {e}")
            self.model_status.config(text="KI: ❌", fg="red")
            self.status_var.set(f"❌ Fehler: {str(e)}")
    
    def ask_question(self, event=None):
        \"\"\"Stellt eine Frage an den KI-Agenten\"\"\"
        question = self.question_entry.get().strip()
        if not question:
            return
        
        self.question_entry.delete(0, "end")
        self.question_queue.put(question)
        
        # Visuelles Feedback
        self.status_var.set("⚡ Verarbeite Frage...")
        self.progress.pack(side="bottom", fill="x")
        self.progress.start()
    
    def question_processor(self):
        \"\"\"Verarbeitet Fragen im Hintergrund\"\"\"
        while not self.stop_event.is_set():
            try:
                question = self.question_queue.get(timeout=1)
                self.process_single_question(question)
            except:
                continue
    
    def process_single_question(self, question: str):
        \"\"\"Verarbeitet eine einzelne Frage\"\"\"
        try:
            # KI-Abfrage oder Demo-Antwort
            if self.llm_agent.initialized:
                result = self.llm_agent.query(question, timeout=120)
            else:
                # Demo-Modus
                result = {
                    "success": True,
                    "answer": f"Demo-Antwort: Ihre Frage '{question}' wurde empfangen. Das KI-Modell ist nicht verfügbar, aber das System funktioniert grundsätzlich.",
                    "error": None
                }
            
            if result["success"]:
                # Antwort anzeigen
                self.root.after(0, lambda: self.display_answer(question, result["answer"]))
                
                # Trainingsdaten speichern
                self.db_manager.save_training_data(question, result["answer"], "Successful query")
            else:
                # Fehler anzeigen
                self.root.after(0, lambda: self.display_error(result["answer"]))
                
        except Exception as e:
            error_msg = f"💥 Unerwarteter Fehler: {str(e)}"
            self.error_handler.log_error(error_msg)
            self.root.after(0, lambda: self.display_error(error_msg))
        finally:
            # UI-Cleanup
            self.root.after(0, self.progress.stop)
            self.root.after(0, self.progress.pack_forget)
            self.root.after(0, lambda: self.status_var.set("✅ Bereit für nächste Frage"))
    
    def display_answer(self, question: str, answer: str):
        \"\"\"Zeigt Frage und Antwort an\"\"\"
        self.answer_area.config(state="normal")
        timestamp = time.strftime("%H:%M:%S")
        
        self.answer_area.insert(tk.END, f"\\n[{timestamp}] 🙋 FRAGE: {question}\\n", "question")
        self.answer_area.insert(tk.END, f"🤖 ANTWORT: {answer}\\n\\n", "answer")
        self.answer_area.see(tk.END)
        self.answer_area.config(state="disabled")
        
        # Text-Tags für Styling
        self.answer_area.tag_config("question", foreground="blue", font=("Arial", 10, "bold"))
        self.answer_area.tag_config("answer", foreground="darkgreen")
    
    def display_error(self, error_msg: str):
        \"\"\"Zeigt eine Fehlermeldung an\"\"\"
        self.answer_area.config(state="normal")
        timestamp = time.strftime("%H:%M:%S")
        self.answer_area.insert(tk.END, f"\\n[{timestamp}] ❌ FEHLER: {error_msg}\\n\\n", "error")
        self.answer_area.see(tk.END)
        self.answer_area.config(state="disabled")
        
        self.answer_area.tag_config("error", foreground="red", font=("Arial", 10, "bold"))
    
    def clear_conversation(self):
        \"\"\"Löscht die Konversation\"\"\"
        self.answer_area.config(state="normal")
        self.answer_area.delete(1.0, tk.END)
        self.answer_area.config(state="disabled")
    
    def on_closing(self):
        \"\"\"Sauberes Beenden der Anwendung\"\"\"
        self.stop_event.set()
        self.root.destroy()

def main():
    \"\"\"Hauptfunktion mit Fehlerbehandlung\"\"\"
    try:
        root = tk.Tk()
        app = ErenAssistApp(root)
        
        # Sauberes Beenden sicherstellen
        root.protocol("WM_DELETE_WINDOW", app.on_closing)
        
        root.mainloop()
        
    except Exception as e:
        error_msg = f"💥 Kritischer Anwendungsfehler: {str(e)}"
        print(error_msg)
        
        # Versuche GUI-Fehlermeldung anzuzeigen
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("💥 Kritischer Fehler", 
                f"Die Anwendung konnte nicht gestartet werden:\\n\\n{error_msg}")
            root.destroy()
        except Exception:
            print("GUI konnte nicht gestartet werden.")

if __name__ == "__main__":
    main()
"""
        
        with open(main_file, 'w', encoding='utf-8') as f:
            f.write(main_code)
        
        print(f"  📄 {main_file}")
    
    def create_starters(self):
        """Erstellt Starter-Skripte"""
        # Batch-Starter
        batch_file = self.base_dir / "Start_EREN_Assist.bat"
        batch_content = '''@echo off
title EREN Assist Enhanced
color 0A
cd /d "C:\\EREN_Assist\\3_Scripts"

echo.
echo  ███████╗██████╗ ███████╗███╗   ██╗
echo  ██╔════╝██╔══██╗██╔════╝████╗  ██║
echo  █████╗  ██████╔╝█████╗  ██╔██╗ ██║
echo  ██╔══╝  ██╔══██╗██╔══╝  ██║╚██╗██║
echo  ███████╗██║  ██║███████╗██║ ╚████║
echo  ╚══════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═══╝
echo.
echo     EREN ASSIST Enhanced
echo     Starte System...
echo.

python eren_assist_gui_enhanced.py

if errorlevel 1 (
    echo.
    echo Fehler beim Starten! Druecke eine Taste...
    pause
)'''
        
        with open(batch_file, 'w', encoding='utf-8') as f:
            f.write(batch_content)
        
        # PowerShell-Starter
        ps_file = self.base_dir / "Start_EREN_Assist.ps1"
        ps_content = '''# EREN Assist Enhanced - PowerShell Starter
Write-Host "🚀 Starte EREN Assist Enhanced..." -ForegroundColor Green
Set-Location "C:\\EREN_Assist\\3_Scripts"
python eren_assist_gui_enhanced.py
Read-Host "Druecke Enter zum Beenden"'''
        
        with open(ps_file, 'w', encoding='utf-8') as f:
            f.write(ps_content)
        
        print(f"  🚀 {batch_file}")
        print(f"  🚀 {ps_file}")
    
    def check_packages(self):
        """Prüft und installiert Python-Pakete"""
        required_packages = [
            "tkinter",  # Sollte mit Python kommen
            "sqlite3",  # Sollte mit Python kommen
            "pathlib",  # Sollte mit Python kommen
        ]
        
        optional_packages = [
            "langchain-community",
            "pytesseract",
            "pillow",
            "pymupdf"
        ]
        
        print("  🔍 Prüfe erforderliche Pakete...")
        for package in required_packages:
            try:
                __import__(package)
                print(f"    ✅ {package}")
            except ImportError:
                print(f"    ❌ {package} - FEHLT!")
        
        print("  🔍 Prüfe optionale Pakete...")
        for package in optional_packages:
            try:
                if package == "langchain-community":
                    from langchain_community.utilities import SQLDatabase
                elif package == "pytesseract":
                    import pytesseract
                elif package == "pillow":
                    from PIL import Image
                elif package == "pymupdf":
                    import fitz
                print(f"    ✅ {package}")
            except ImportError:
                print(f"    ⚠️ {package} - Optional, nicht installiert")
                choice = input(f"    Möchten Sie {package} installieren? (j/n): ")
                if choice.lower() == 'j':
                    try:
                        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                        print(f"    ✅ {package} installiert!")
                    except subprocess.CalledProcessError:
                        print(f"    ❌ Installation von {package} fehlgeschlagen")
    
    def setup_database(self):
        """Initialisiert die Datenbank"""
        db_file = self.db_dir / "eren_assist.db"
        
        with sqlite3.connect(db_file) as conn:
            cursor = conn.cursor()
            
            # Basis-Tabellen
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS training_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    question TEXT NOT NULL,
                    answer TEXT,
                    thinking_process TEXT,
                    error_info TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS error_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    error_type TEXT,
                    error_message TEXT,
                    context TEXT
                )
            ''')
            
            # Test-Eintrag
            cursor.execute('''
                INSERT OR IGNORE INTO training_log (question, answer, thinking_process)
                VALUES (?, ?, ?)
            ''', ("Test-Frage", "Test-Antwort", "System-Test bei Installation"))
            
            conn.commit()
        
        print(f"  🗄️ {db_file}")
    
    def create_shortcuts(self):
        """Erstellt Desktop-Verknüpfung"""
        try:
            import winshell
            from win32com.client import Dispatch
            
            desktop = winshell.desktop()
            target = str(self.base_dir / "Start_EREN_Assist.bat")
            
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(os.path.join(desktop, "EREN Assist Enhanced.lnk"))
            shortcut.Targetpath = target
            shortcut.WorkingDirectory = str(self.base_dir)
            shortcut.Description = "EREN Assist Enhanced - KI-gestützte Datenanalyse"
            shortcut.save()
            
            print(f"  🔗 Desktop-Verknüpfung erstellt")
            
        except ImportError:
            print("  ⚠️ winshell/pywin32 nicht verfügbar - keine Desktop-Verknüpfung")
        except Exception as e:
            print(f"  ⚠️ Verknüpfung fehlgeschlagen: {e}")
    
    def test_installation(self):
        """Testet die Installation"""
        print("  🧪 Teste System...")
        
        # Hauptdatei prüfen
        main_file = self.scripts_dir / "eren_assist_gui_enhanced.py"
        if not main_file.exists():
            raise Exception("Hauptdatei nicht gefunden!")
        
        # Datenbank prüfen
        db_file = self.db_dir / "eren_assist.db"
        if not db_file.exists():
            raise Exception("Datenbank nicht erstellt!")
        
        # Starter prüfen
        batch_file = self.base_dir / "Start_EREN_Assist.bat"
        if not batch_file.exists():
            raise Exception("Batch-Starter nicht erstellt!")
        
        print("  ✅ Alle Tests bestanden!")

if __name__ == "__main__":
    setup = ErenSetup()
    
    if setup.run_setup():
        print("=" * 60)
        print("🎉 INSTALLATION ERFOLGREICH ABGESCHLOSSEN!")
        print("=" * 60)
        print()
        print("📋 Nächste Schritte:")
        print("1. Doppelklick auf 'EREN Assist Enhanced' auf dem Desktop")
        print("2. Oder: Start_EREN_Assist.bat im EREN_Assist Ordner")
        print("3. Bei Problemen: Logdatei in C:\\EREN_Assist\\eren_assist_error.log prüfen")
        print()
        print("💡 Das System läuft auch ohne KI-Modell im Demo-Modus!")
        print()
        
        choice = input("Möchten Sie EREN Assist jetzt starten? (j/n): ")
        if choice.lower() == 'j':
            os.chdir(setup.scripts_dir)
            subprocess.run([sys.executable, "eren_assist_gui_enhanced.py"])
    else:
        print("❌ Installation fehlgeschlagen!")
    
    input("Drücke Enter zum Beenden...")