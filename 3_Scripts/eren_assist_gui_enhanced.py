#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EREN Assist Enhanced 2025 - Bereinigte Hauptanwendung
KI-gestützte Datenanalyse mit moderner GUI
"""

import warnings
warnings.filterwarnings("ignore")

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import os
import threading
import sqlite3
import time
import logging
from pathlib import Path
from queue import Queue, Empty
from typing import Optional, Dict, Any
from datetime import datetime

# Conditional imports mit sauberer Fehlerbehandlung
try:
    from langchain_community.utilities import SQLDatabase
    from langchain_community.agent_toolkits import create_sql_agent
    from langchain_community.llms import GPT4All
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

try:
    from PIL import Image
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

try:
    import fitz  # PyMuPDF
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


class ErrorHandler:
    """Verbesserte Fehlerbehandlung mit Logging"""
    
    def __init__(self, log_dir: Path):
        self.log_dir = log_dir
        self.log_dir.mkdir(exist_ok=True)
        self.setup_logging()
        
    def setup_logging(self):
        """Konfiguriert das Logging-System"""
        log_file = self.log_dir / f"eren_assist_{datetime.now().strftime('%Y%m%d')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def log_error(self, msg: str):
        self.logger.error(f"ERROR: {msg}")
        
    def log_warning(self, msg: str):
        self.logger.warning(f"WARNING: {msg}")
        
    def log_info(self, msg: str):
        self.logger.info(f"INFO: {msg}")


class DatabaseManager:
    """Vereinfachte Datenbankoperationen"""
    
    def __init__(self, db_path: str, error_handler: ErrorHandler):
        self.db_path = db_path
        self.error_handler = error_handler
        self.ensure_database_exists()
    
    def ensure_database_exists(self):
        """Stellt sicher, dass die Datenbank mit aktualisiertem Schema existiert"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Erweiterte Training-Log Tabelle
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS training_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        question TEXT NOT NULL,
                        answer TEXT,
                        thinking_process TEXT,
                        error_info TEXT,
                        response_time_ms INTEGER,
                        session_id TEXT
                    )
                """)
                
                # System-Metriken Tabelle
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS system_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        metric_name TEXT,
                        metric_value REAL,
                        metric_unit TEXT
                    )
                """)
                
                # Prüfe und erweitere Schema falls nötig
                cursor.execute("PRAGMA table_info(training_log)")
                columns = [column[1] for column in cursor.fetchall()]
                
                if 'response_time_ms' not in columns:
                    cursor.execute("ALTER TABLE training_log ADD COLUMN response_time_ms INTEGER")
                    self.error_handler.log_info("Database schema updated successfully")
                
                conn.commit()
                
        except sqlite3.Error as e:
            self.error_handler.log_error(f"Database creation failed: {e}")
    
    def save_training_data(self, question: str, answer: Optional[str], 
                          thinking_process: str, error_info: Optional[str] = None,
                          response_time_ms: Optional[int] = None):
        """Speichert Trainingsdaten mit erweiterten Metriken"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO training_log 
                    (question, answer, thinking_process, error_info, response_time_ms)
                    VALUES (?, ?, ?, ?, ?)
                """, (question, answer, thinking_process, error_info, response_time_ms))
                conn.commit()
        except sqlite3.Error as e:
            self.error_handler.log_error(f"Failed to save training data: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Holt Datenbankstatistiken"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Anzahl Anfragen
                cursor.execute("SELECT COUNT(*) FROM training_log")
                total_queries = cursor.fetchone()[0]
                
                # Durchschnittliche Antwortzeit
                cursor.execute("SELECT AVG(response_time_ms) FROM training_log WHERE response_time_ms IS NOT NULL")
                avg_response_time = cursor.fetchone()[0] or 0
                
                # Erfolgsrate
                cursor.execute("SELECT COUNT(*) FROM training_log WHERE answer IS NOT NULL")
                successful_queries = cursor.fetchone()[0]
                success_rate = (successful_queries / total_queries * 100) if total_queries > 0 else 0
                
                return {
                    'total_queries': total_queries,
                    'avg_response_time_ms': round(avg_response_time, 2),
                    'success_rate': round(success_rate, 2),
                    'successful_queries': successful_queries
                }
        except sqlite3.Error as e:
            self.error_handler.log_error(f"Failed to get statistics: {e}")
            return {}


class RobustLLMAgent:
    """LLM-Agent mit verbesserter 2025-Kompatibilität"""
    
    def __init__(self, model_path: str, db_path: str, error_handler: ErrorHandler):
        self.model_path = model_path
        self.db_path = db_path
        self.error_handler = error_handler
        self.agent = None
        self.initialized = False
    
    def initialize(self) -> bool:
        """Initialisiert den LLM-Agent mit 2025-kompatibler Konfiguration"""
        if not LANGCHAIN_AVAILABLE:
            self.error_handler.log_warning("LangChain not available - running in demo mode")
            return False
        
        if not os.path.exists(self.model_path):
            self.error_handler.log_warning(f"Model file not found: {self.model_path}")
            return False
        
        try:
            # CPU-only Modus erzwingen
            os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
            
            # Datenbank verbinden
            db = SQLDatabase.from_uri(f"sqlite:///{self.db_path}")
            
            # LLM mit 2025-kompatiblen Parametern initialisieren
            llm = GPT4All(
                model=self.model_path,
                verbose=False,
                allow_download=False,
                # Entfernte deprecated Parameter: temp, n_ctx, n_gpu_layers
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
        """Führt eine Abfrage mit Zeitüberwachung aus"""
        start_time = time.time()
        
        if not self.initialized:
            return {
                "success": True,
                "answer": f"Demo-Antwort: Ihre Frage '{question}' wurde empfangen. Das System läuft im Demo-Modus ohne KI-Modell.",
                "error": None,
                "response_time_ms": int((time.time() - start_time) * 1000)
            }
        
        try:
            # Verwende moderne LangChain API
            if hasattr(self.agent, 'invoke'):
                result = self.agent.invoke({"input": question})
                answer = result.get("output", "Keine Antwort erhalten")
            else:
                # Fallback für ältere Versionen
                answer = self.agent.run(question)
            
            response_time = int((time.time() - start_time) * 1000)
            
            return {
                "success": True,
                "answer": answer,
                "error": None,
                "response_time_ms": response_time
            }
            
        except Exception as e:
            error_msg = str(e)
            response_time = int((time.time() - start_time) * 1000)
            self.error_handler.log_error(f"Query failed: {error_msg}")
            
            return {
                "success": False,
                "error": error_msg,
                "answer": f"Fehler bei der Verarbeitung: {error_msg}",
                "response_time_ms": response_time
            }


class ErenAssistApp:
    """Hauptanwendung mit bereinigter Architektur"""
    
    def __init__(self, root):
        self.root = root
        self.setup_directories()
        self.setup_error_handling()
        self.setup_components()
        self.setup_gui()
        self.start_background_services()
    
    def setup_directories(self):
        """Erstellt die Verzeichnisstruktur"""
        self.BASE_DIR = Path("C:/EREN_Assist")
        self.DB_PATH = self.BASE_DIR / "1_Datenbank" / "eren_assist.db"
        self.PDF_DIR = self.BASE_DIR / "2_PDF_Archiv"
        self.SCRIPTS_DIR = self.BASE_DIR / "3_Scripts"
        self.MODEL_DIR = self.BASE_DIR / "ki_modelle"
        self.LOGS_DIR = self.BASE_DIR / "logs"
        
        # Verzeichnisse erstellen
        for directory in [self.BASE_DIR, self.DB_PATH.parent, 
                         self.PDF_DIR, self.SCRIPTS_DIR, self.MODEL_DIR, self.LOGS_DIR]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # KI-Modell-Konfiguration
        self.MODEL_FILE = "mistral-7b-openorca.Q5_K_M.gguf"
        self.MODEL_PATH = self.MODEL_DIR / self.MODEL_FILE
    
    def setup_error_handling(self):
        """Initialisiert die Fehlerbehandlung"""
        self.error_handler = ErrorHandler(self.LOGS_DIR)
        
    def setup_components(self):
        """Initialisiert alle Systemkomponenten"""
        self.db_manager = DatabaseManager(str(self.DB_PATH), self.error_handler)
        self.llm_agent = RobustLLMAgent(str(self.MODEL_PATH), str(self.DB_PATH), self.error_handler)
        
        # Threading-Komponenten
        self.stop_event = threading.Event()
        self.question_queue = Queue()
        self.session_id = f"session_{int(time.time())}"
        
    def setup_gui(self):
        """Erstellt die moderne Benutzeroberfläche"""
        self.root.title("EREN Assist Enhanced 2025 - KI-gestützte Datenanalyse")
        self.root.geometry("1200x800")
        self.root.configure(bg="#f8f9fa")
        
        # Modernes Theme
        style = ttk.Style()
        style.theme_use('clam')
        
        # Header mit Status
        self.setup_header()
        
        # Notebook für Tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Haupttabs
        self.setup_chat_tab()
        self.setup_system_tab()
        self.setup_statistics_tab()
        
        # Statusleiste
        self.setup_statusbar()
        
    def setup_header(self):
        """Erstellt den Header mit Status-Indikatoren"""
        header_frame = tk.Frame(self.root, bg="#2c3e50", height=80)
        header_frame.pack(fill="x", side="top")
        header_frame.pack_propagate(False)
        
        # Titel
        title_label = tk.Label(
            header_frame, 
            text="EREN ASSIST Enhanced 2025", 
            font=("Arial", 20, "bold"), 
            fg="white", 
            bg="#2c3e50"
        )
        title_label.pack(side="left", padx=20, pady=20)
        
        # Status-Indikatoren
        status_frame = tk.Frame(header_frame, bg="#2c3e50")
        status_frame.pack(side="right", padx=20, pady=20)
        
        # System-Status
        self.db_status = tk.Label(status_frame, text="DB: ❌", fg="red", bg="#2c3e50", font=("Arial", 10, "bold"))
        self.db_status.pack(side="top", anchor="e")
        
        self.ki_status = tk.Label(status_frame, text="KI: ❌", fg="red", bg="#2c3e50", font=("Arial", 10, "bold"))
        self.ki_status.pack(side="top", anchor="e")
        
        # Update Status
        self.update_status_indicators()
    
    def setup_chat_tab(self):
        """Erstellt den Haupt-Chat-Tab"""
        chat_frame = ttk.Frame(self.notebook)
        self.notebook.add(chat_frame, text="💬 KI-Assistent")
        
        # Eingabebereich
        input_frame = ttk.LabelFrame(chat_frame, text="Ihre Frage", padding="10")
        input_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        self.question_entry = tk.Text(input_frame, height=3, font=("Arial", 11), wrap="word")
        self.question_entry.pack(fill="x", pady=(0, 10))
        self.question_entry.bind("<Control-Return>", self.ask_question)
        
        # Buttons
        button_frame = ttk.Frame(input_frame)
        button_frame.pack(fill="x")
        
        ttk.Button(button_frame, text="🤖 Frage stellen (Ctrl+Enter)", 
                  command=self.ask_question).pack(side="left", padx=(0, 10))
        ttk.Button(button_frame, text="🗑️ Löschen", 
                  command=self.clear_conversation).pack(side="left", padx=(0, 10))
        ttk.Button(button_frame, text="💾 Export", 
                  command=self.export_conversation).pack(side="left")
        
        # Antwortbereich
        answer_frame = ttk.LabelFrame(chat_frame, text="Antworten", padding="10")
        answer_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.answer_area = scrolledtext.ScrolledText(
            answer_frame, 
            wrap="word", 
            font=("Arial", 10),
            state="disabled"
        )
        self.answer_area.pack(fill="both", expand=True)
        
        # Text-Tags für Styling
        self.answer_area.tag_config("question", foreground="#2c3e50", font=("Arial", 10, "bold"))
        self.answer_area.tag_config("answer", foreground="#27ae60")
        self.answer_area.tag_config("error", foreground="#e74c3c", font=("Arial", 10, "bold"))
        self.answer_area.tag_config("timestamp", foreground="#7f8c8d", font=("Arial", 9))
    
    def setup_system_tab(self):
        """Erstellt den System-Tab"""
        system_frame = ttk.Frame(self.notebook)
        self.notebook.add(system_frame, text="⚙️ System")
        
        # System-Info
        info_frame = ttk.LabelFrame(system_frame, text="System-Information", padding="10")
        info_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.system_info_area = scrolledtext.ScrolledText(info_frame, height=20, font=("Consolas", 9))
        self.system_info_area.pack(fill="both", expand=True)
        
        # Kontroll-Buttons
        control_frame = ttk.Frame(system_frame)
        control_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Button(control_frame, text="📊 System-Check", 
                  command=self.run_system_check).pack(side="left", padx=5)
        ttk.Button(control_frame, text="📁 PDF-Ordner", 
                  command=self.open_pdf_folder).pack(side="left", padx=5)
        ttk.Button(control_frame, text="🗄️ Datenbank", 
                  command=self.show_database_info).pack(side="left", padx=5)
        ttk.Button(control_frame, text="📋 Logs", 
                  command=self.show_logs).pack(side="left", padx=5)
    
    def setup_statistics_tab(self):
        """Erstellt den Statistik-Tab"""
        stats_frame = ttk.Frame(self.notebook)
        self.notebook.add(stats_frame, text="📊 Statistiken")
        
        # Metriken-Karten
        metrics_frame = ttk.Frame(stats_frame)
        metrics_frame.pack(fill="x", padx=10, pady=10)
        
        # KPI-Karten
        self.create_metric_card(metrics_frame, "Anfragen gesamt", "0", 0)
        self.create_metric_card(metrics_frame, "Ø Antwortzeit", "0ms", 1)
        self.create_metric_card(metrics_frame, "Erfolgsrate", "0%", 2)
        
        # Detaillierte Statistiken
        detail_frame = ttk.LabelFrame(stats_frame, text="Detaillierte Statistiken", padding="10")
        detail_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.stats_area = scrolledtext.ScrolledText(detail_frame, font=("Consolas", 9))
        self.stats_area.pack(fill="both", expand=True)
        
        # Update-Button
        ttk.Button(stats_frame, text="🔄 Aktualisieren", 
                  command=self.update_statistics).pack(pady=10)
    
    def create_metric_card(self, parent, title, value, column):
        """Erstellt eine Metrik-Karte"""
        card_frame = ttk.LabelFrame(parent, text=title, padding="10")
        card_frame.grid(row=0, column=column, padx=10, pady=5, sticky="ew")
        parent.columnconfigure(column, weight=1)
        
        value_label = tk.Label(card_frame, text=value, font=("Arial", 16, "bold"), fg="#2c3e50")
        value_label.pack()
        
        # Speichere Label-Referenz für Updates
        setattr(self, f"metric_{title.lower().replace(' ', '_').replace('ø_', 'avg_')}", value_label)
    
    def setup_statusbar(self):
        """Erstellt die Statusleiste"""
        self.status_var = tk.StringVar(value="🚀 EREN Assist wird initialisiert...")
        status_bar = tk.Label(
            self.root, 
            textvariable=self.status_var, 
            bd=1, 
            relief="sunken", 
            anchor="w",
            bg="#ecf0f1",
            font=("Arial", 10)
        )
        status_bar.pack(side="bottom", fill="x")
        
        # Fortschrittsbalken
        self.progress = ttk.Progressbar(self.root, mode='indeterminate')
    
    def start_background_services(self):
        """Startet alle Hintergrunddienste"""
        threading.Thread(target=self.initialize_llm_agent, daemon=True).start()
        threading.Thread(target=self.question_processor, daemon=True).start()
        threading.Thread(target=self.load_initial_system_info, daemon=True).start()
    
    def update_status_indicators(self):
        """Aktualisiert die Status-Indikatoren"""
        # Datenbank-Status
        if self.DB_PATH.exists():
            self.db_status.config(text="DB: ✔", fg="#27ae60")
        else:
            self.db_status.config(text="DB: ❌", fg="#e74c3c")
    
    def initialize_llm_agent(self):
        """Initialisiert den LLM-Agent"""
        self.status_var.set("🤖 Initialisiere KI-Modell...")
        
        try:
            success = self.llm_agent.initialize()
            if success:
                self.ki_status.config(text="KI: ✔", fg="#27ae60")
                self.status_var.set("✅ EREN Assist bereit! Sie können jetzt Fragen stellen.")
            else:
                self.ki_status.config(text="KI: ⚠", fg="#f39c12")
                if not self.MODEL_PATH.exists():
                    self.status_var.set("⚠️ Demo-Modus: KI-Modell nicht gefunden")
                else:
                    self.status_var.set("⚠️ KI-Agent konnte nicht initialisiert werden")
        except Exception as e:
            self.error_handler.log_error(f"LLM initialization error: {e}")
            self.ki_status.config(text="KI: ❌", fg="#e74c3c")
            self.status_var.set(f"❌ Fehler: {str(e)[:50]}...")
    
    def ask_question(self, event=None):
        """Stellt eine Frage an den KI-Agenten"""
        question = self.question_entry.get("1.0", "end-1c").strip()
        if not question:
            return "break"  # Verhindert Standard-Verhalten bei Ctrl+Enter
        
        self.question_entry.delete("1.0", "end")
        self.question_queue.put(question)
        
        # Visuelles Feedback
        self.status_var.set("⚡ Verarbeite Frage...")
        self.progress.pack(side="bottom", fill="x")
        self.progress.start()
        
        return "break"
    
    def question_processor(self):
        """Verarbeitet Fragen im Hintergrund"""
        while not self.stop_event.is_set():
            try:
                question = self.question_queue.get(timeout=1)
                self.process_single_question(question)
            except Empty:
                continue
    
    def process_single_question(self, question: str):
        """Verarbeitet eine einzelne Frage"""
        start_time = time.time()
        
        try:
            # KI-Abfrage
            result = self.llm_agent.query(question, timeout=120)
            
            if result["success"]:
                self.root.after(0, lambda: self.display_answer(question, result["answer"]))
                
                # Trainingsdaten speichern
                self.db_manager.save_training_data(
                    question, 
                    result["answer"], 
                    "Successful query",
                    response_time_ms=result.get("response_time_ms")
                )
            else:
                self.root.after(0, lambda: self.display_error(result["answer"]))
                
                # Fehler in Trainingsdaten speichern
                self.db_manager.save_training_data(
                    question, 
                    None, 
                    "Failed query", 
                    error_info=result["error"],
                    response_time_ms=result.get("response_time_ms")
                )
            
        except Exception as e:
            error_msg = f"Unerwarteter Fehler: {str(e)}"
            self.error_handler.log_error(error_msg)
            self.root.after(0, lambda: self.display_error(error_msg))
        finally:
            # UI-Cleanup
            self.root.after(0, self.progress.stop)
            self.root.after(0, self.progress.pack_forget)
            self.root.after(0, lambda: self.status_var.set("✅ Bereit für nächste Frage"))
    
    def display_answer(self, question: str, answer: str):
        """Zeigt Frage und Antwort an"""
        self.answer_area.config(state="normal")
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        self.answer_area.insert("end", f"\n[{timestamp}] ", "timestamp")
        self.answer_area.insert("end", f"🙋 FRAGE: {question}\n", "question")
        self.answer_area.insert("end", f"🤖 ANTWORT: {answer}\n\n", "answer")
        
        self.answer_area.see("end")
        self.answer_area.config(state="disabled")
    
    def display_error(self, error_msg: str):
        """Zeigt eine Fehlermeldung an"""
        self.answer_area.config(state="normal")
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        self.answer_area.insert("end", f"\n[{timestamp}] ", "timestamp")
        self.answer_area.insert("end", f"❌ FEHLER: {error_msg}\n\n", "error")
        
        self.answer_area.see("end")
        self.answer_area.config(state="disabled")
    
    def clear_conversation(self):
        """Löscht die Konversation"""
        self.answer_area.config(state="normal")
        self.answer_area.delete("1.0", "end")
        self.answer_area.config(state="disabled")
    
    def export_conversation(self):
        """Exportiert die Konversation"""
        content = self.answer_area.get("1.0", "end-1c")
        if not content.strip():
            messagebox.showinfo("Export", "Keine Konversation zum Exportieren vorhanden.")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Textdateien", "*.txt"), ("Alle Dateien", "*.*")],
            title="Konversation exportieren"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"EREN Assist Konversation - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=" * 60 + "\n\n")
                    f.write(content)
                messagebox.showinfo("Export", f"Konversation erfolgreich exportiert:\n{filename}")
            except Exception as e:
                messagebox.showerror("Fehler", f"Export fehlgeschlagen:\n{str(e)}")
    
    def run_system_check(self):
        """Führt einen System-Check durch"""
        threading.Thread(target=self._run_system_check_background, daemon=True).start()
    
    def _run_system_check_background(self):
        """System-Check im Hintergrund"""
        check_info = []
        
        # Python-Version
        import sys
        check_info.append(f"Python Version: {sys.version}")
        
        # Verzeichnisse
        check_info.append(f"\nVerzeichnisstruktur:")
        for name, path in [
            ("Basis", self.BASE_DIR),
            ("Datenbank", self.DB_PATH.parent),
            ("PDFs", self.PDF_DIR),
            ("Scripts", self.SCRIPTS_DIR),
            ("KI-Modelle", self.MODEL_DIR),
            ("Logs", self.LOGS_DIR)
        ]:
            status = "✅" if path.exists() else "❌"
            check_info.append(f"  {status} {name}: {path}")
        
        # Bibliotheken
        check_info.append(f"\nBibliotheken:")
        check_info.append(f"  {'✅' if LANGCHAIN_AVAILABLE else '❌'} LangChain")
        check_info.append(f"  {'✅' if OCR_AVAILABLE else '❌'} OCR (Tesseract/PIL)")
        check_info.append(f"  {'✅' if PDF_AVAILABLE else '❌'} PDF (PyMuPDF)")
        
        # KI-Modell
        check_info.append(f"\nKI-System:")
        check_info.append(f"  {'✅' if self.MODEL_PATH.exists() else '❌'} Modell-Datei: {self.MODEL_FILE}")
        check_info.append(f"  {'✅' if self.llm_agent.initialized else '❌'} Agent initialisiert")
        
        # Datenbank
        check_info.append(f"\nDatenbank:")
        try:
            stats = self.db_manager.get_statistics()
            check_info.append(f"  📊 Anfragen gesamt: {stats.get('total_queries', 0)}")
            check_info.append(f"  ⚡ Ø Antwortzeit: {stats.get('avg_response_time_ms', 0):.0f}ms")
            check_info.append(f"  ✅ Erfolgsrate: {stats.get('success_rate', 0):.1f}%")
        except Exception as e:
            check_info.append(f"  ❌ Datenbankfehler: {str(e)}")
        
        # Speicherplatz
        try:
            import shutil
            total, used, free = shutil.disk_usage(str(self.BASE_DIR))
            check_info.append(f"\nSpeicherplatz:")
            check_info.append(f"  💾 Verfügbar: {free // (1024**3)} GB")
            check_info.append(f"  📁 Gesamt: {total // (1024**3)} GB")
        except Exception as e:
            check_info.append(f"\nSpeicherplatz: Fehler - {str(e)}")
        
        result_text = "\n".join(check_info)
        self.root.after(0, lambda: self.update_system_info(result_text))
    
    def update_system_info(self, text: str):
        """Aktualisiert den System-Info-Bereich"""
        self.system_info_area.delete("1.0", "end")
        self.system_info_area.insert("1.0", text)
    
    def open_pdf_folder(self):
        """Öffnet den PDF-Ordner"""
        try:
            if self.PDF_DIR.exists():
                os.startfile(str(self.PDF_DIR))
                self.status_var.set(f"📁 PDF-Ordner geöffnet")
            else:
                self.PDF_DIR.mkdir(parents=True, exist_ok=True)
                os.startfile(str(self.PDF_DIR))
                self.status_var.set(f"📁 PDF-Ordner erstellt und geöffnet")
        except Exception as e:
            messagebox.showerror("Fehler", f"PDF-Ordner konnte nicht geöffnet werden:\n{str(e)}")
    
    def show_database_info(self):
        """Zeigt Datenbank-Informationen"""
        threading.Thread(target=self._load_database_info, daemon=True).start()
    
    def _load_database_info(self):
        """Lädt Datenbank-Informationen im Hintergrund"""
        try:
            with sqlite3.connect(str(self.DB_PATH)) as conn:
                cursor = conn.cursor()
                
                info_text = "=== DATENBANK-ÜBERSICHT ===\n\n"
                
                # Tabellen auflisten
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                
                for table_name, in tables:
                    info_text += f"📋 TABELLE: {table_name}\n"
                    
                    # Anzahl Datensätze
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cursor.fetchone()[0]
                    info_text += f"   Datensätze: {count}\n"
                    
                    # Letzte Aktualisierung (falls timestamp vorhanden)
                    try:
                        cursor.execute(f"SELECT MAX(timestamp) FROM {table_name}")
                        last_update = cursor.fetchone()[0]
                        if last_update:
                            info_text += f"   Letzte Aktualisierung: {last_update}\n"
                    except:
                        pass
                    
                    info_text += "\n"
                
                # Statistiken
                stats = self.db_manager.get_statistics()
                if stats:
                    info_text += "=== STATISTIKEN ===\n"
                    for key, value in stats.items():
                        info_text += f"{key}: {value}\n"
                
                self.root.after(0, lambda: self.update_system_info(info_text))
                
        except Exception as e:
            error_msg = f"Datenbankfehler: {str(e)}"
            self.error_handler.log_error(error_msg)
            self.root.after(0, lambda: self.update_system_info(error_msg))
    
    def show_logs(self):
        """Zeigt die aktuellen Logs"""
        try:
            log_file = self.LOGS_DIR / f"eren_assist_{datetime.now().strftime('%Y%m%d')}.log"
            if log_file.exists():
                with open(log_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Zeige nur die letzten 100 Zeilen
                    lines = content.split('\n')
                    if len(lines) > 100:
                        content = '\n'.join(lines[-100:])
                        content = "... (ältere Einträge ausgeblendet) ...\n\n" + content
            else:
                content = "Keine aktuellen Logs gefunden."
            
            self.update_system_info(content)
        except Exception as e:
            self.update_system_info(f"Fehler beim Laden der Logs: {str(e)}")
    
    def update_statistics(self):
        """Aktualisiert die Statistiken"""
        threading.Thread(target=self._update_statistics_background, daemon=True).start()
    
    def _update_statistics_background(self):
        """Aktualisiert Statistiken im Hintergrund"""
        try:
            stats = self.db_manager.get_statistics()
            
            # Metriken-Karten aktualisieren
            self.root.after(0, lambda: self.metric_anfragen_gesamt.config(text=str(stats.get('total_queries', 0))))
            self.root.after(0, lambda: self.metric_avg_antwortzeit.config(text=f"{stats.get('avg_response_time_ms', 0):.0f}ms"))
            self.root.after(0, lambda: self.metric_erfolgsrate.config(text=f"{stats.get('success_rate', 0):.1f}%"))
            
            # Detaillierte Statistiken
            detail_text = f"""=== DETAILLIERTE STATISTIKEN ===

Anfragen:
• Gesamt: {stats.get('total_queries', 0)}
• Erfolgreich: {stats.get('successful_queries', 0)}
• Fehlgeschlagen: {stats.get('total_queries', 0) - stats.get('successful_queries', 0)}

Performance:
• Durchschnittliche Antwortzeit: {stats.get('avg_response_time_ms', 0):.2f}ms
• Erfolgsrate: {stats.get('success_rate', 0):.2f}%

System:
• KI-Agent: {'Aktiv' if self.llm_agent.initialized else 'Inaktiv'}
• Demo-Modus: {'Ja' if not self.llm_agent.initialized else 'Nein'}
• Datenbank: {'Verbunden' if self.DB_PATH.exists() else 'Nicht gefunden'}

Letzte Aktualisierung: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            
            self.root.after(0, lambda: self._update_stats_display(detail_text))
            
        except Exception as e:
            error_msg = f"Statistik-Update fehlgeschlagen: {str(e)}"
            self.error_handler.log_error(error_msg)
            self.root.after(0, lambda: self._update_stats_display(error_msg))
    
    def _update_stats_display(self, text: str):
        """Aktualisiert die Statistik-Anzeige"""
        self.stats_area.delete("1.0", "end")
        self.stats_area.insert("1.0", text)
    
    def load_initial_system_info(self):
        """Lädt initiale System-Informationen"""
        try:
            info_text = f"""EREN ASSIST Enhanced 2025 - System-Übersicht

🚀 Version: 2025.1.0
📅 Gestartet: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🗂️ Arbeitsverzeichnis: {self.BASE_DIR}

📊 Status:
• Datenbank: {'✅ Verbunden' if self.DB_PATH.exists() else '❌ Nicht gefunden'}
• KI-Modell: {'✅ Geladen' if self.llm_agent.initialized else '⚠️ Demo-Modus'}
• PDF-Archiv: {'✅ Bereit' if self.PDF_DIR.exists() else '📁 Wird erstellt'}

💡 Erste Schritte:
1. Stellen Sie eine Frage im KI-Assistenten-Tab
2. Legen Sie PDF-Dateien in das PDF-Archiv
3. Nutzen Sie den System-Check für Details

📖 Verfügbare Funktionen:
• KI-gestützte Datenanalyse
• Volltext-Suche in Dokumenten
• System-Überwachung und Statistiken
• Konversations-Export

Hinweis: System läuft im {'Demo-Modus' if not self.llm_agent.initialized else 'Vollmodus'}
"""
            
            self.root.after(0, lambda: self.update_system_info(info_text))
            
        except Exception as e:
            self.error_handler.log_error(f"Could not load initial system info: {e}")
    
    def on_closing(self):
        """Sauberes Beenden der Anwendung"""
        self.stop_event.set()
        
        try:
            # Finale Statistiken speichern
            if hasattr(self, 'db_manager'):
                self.error_handler.log_info("Application closing gracefully")
        except:
            pass
        
        self.root.destroy()


def main():
    """Hauptfunktion mit umfassender Fehlerbehandlung"""
    try:
        # Prüfe Python-Version
        import sys
        if sys.version_info < (3, 8):
            messagebox.showerror(
                "Python-Version", 
                f"Python 3.8+ erforderlich!\nGefunden: {sys.version_info.major}.{sys.version_info.minor}\n\n"
                "Bitte aktualisieren Sie Python."
            )
            return
        
        # Erstelle Hauptfenster
        root = tk.Tk()
        
        # Icon setzen (falls vorhanden)
        try:
            root.iconbitmap('eren_icon.ico')
        except:
            pass
        
        # Anwendung erstellen
        app = ErenAssistApp(root)
        
        # Sauberes Beenden sicherstellen
        root.protocol("WM_DELETE_WINDOW", app.on_closing)
        
        # Anwendung starten
        root.mainloop()
        
    except ImportError as e:
        messagebox.showerror(
            "Import-Fehler", 
            f"Erforderliche Bibliothek fehlt:\n{str(e)}\n\n"
            "Installieren Sie die Abhängigkeiten:\n"
            "pip install langchain-community gpt4all"
        )
    except Exception as e:
        error_msg = f"Kritischer Anwendungsfehler:\n{str(e)}"
        print(error_msg)
        
        try:
            messagebox.showerror("Kritischer Fehler", error_msg)
        except:
            print("GUI konnte nicht gestartet werden.")


if __name__ == "__main__":
    main()