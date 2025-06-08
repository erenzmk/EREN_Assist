#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EREN Assist - Aktualisierte Version 2025
Kompatibel mit den neuesten LangChain APIs und behebt alle bekannten Probleme
"""

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
import sys
import tempfile

# Conditional imports mit besserer Fehlerbehandlung
try:
    from langchain_community.utilities import SQLDatabase
    from langchain_community.agent_toolkits import create_sql_agent
    from langchain_community.llms import GPT4All
    LANGCHAIN_AVAILABLE = True
    LANGCHAIN_VERSION = "2025"
except ImportError:
    LANGCHAIN_AVAILABLE = False
    LANGCHAIN_VERSION = "none"

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
    """Erweiterte Fehlerbehandlung mit besserer Logging-Strategie"""
    
    def __init__(self, log_file: str):
        self.log_file = log_file
        self.setup_logging()
    
    def setup_logging(self):
        """Konfiguriert das Logging-System"""
        import logging
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
        """Protokolliert Fehler mit Kontext"""
        self.logger.error(f"{error_type}: {error_msg}")
        
    def log_warning(self, warning_msg: str):
        """Protokolliert Warnungen"""
        self.logger.warning(warning_msg)
        
    def log_info(self, info_msg: str):
        """Protokolliert Informationen"""
        self.logger.info(info_msg)

class DatabaseManager:
    """Verbesserte Datenbankoperationen - 2025 Version"""
    
    def __init__(self, db_path: str, error_handler: ErrorHandler):
        self.db_path = db_path
        self.error_handler = error_handler
        self.ensure_database_exists()
    
    def ensure_database_exists(self):
        """Stellt sicher, dass die Datenbank mit korrektem Schema existiert"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Erweiterte Tabelle für Training-Logs
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS training_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        question TEXT NOT NULL,
                        answer TEXT,
                        thinking_process TEXT,
                        error_info TEXT,
                        model_version TEXT,
                        response_time_ms INTEGER
                    )
                """)
                
                # System-Status Tabelle
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS system_status (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        component TEXT,
                        status TEXT,
                        details TEXT
                    )
                """)
                
                # Performance-Metriken
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS performance_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        metric_name TEXT,
                        metric_value REAL,
                        metric_unit TEXT
                    )
                """)
                
                conn.commit()
                self.error_handler.log_info("Database schema updated successfully")
                
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
                    (question, answer, thinking_process, error_info, model_version, response_time_ms)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (question, answer, thinking_process, error_info, 
                     f"EREN-2025-v{LANGCHAIN_VERSION}", response_time_ms))
                conn.commit()
        except sqlite3.Error as e:
            self.error_handler.log_error(f"Failed to save training data: {e}")
    
    def log_system_status(self, component: str, status: str, details: str = ""):
        """Protokolliert System-Status"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO system_status (component, status, details)
                    VALUES (?, ?, ?)
                """, (component, status, details))
                conn.commit()
        except sqlite3.Error as e:
            self.error_handler.log_error(f"Failed to log system status: {e}")

class ModernLLMAgent:
    """Modernisierter LLM-Agent kompatibel mit LangChain 2025"""
    
    def __init__(self, model_path: str, db_path: str, error_handler: ErrorHandler):
        self.model_path = model_path
        self.db_path = db_path
        self.error_handler = error_handler
        self.agent = None
        self.llm = None
        self.initialized = False
        self.demo_mode = False
    
    def initialize(self) -> bool:
        """Initialisiert den LLM-Agent mit modernen APIs"""
        if not LANGCHAIN_AVAILABLE:
            self.error_handler.log_error("LangChain not available - running in demo mode")
            self.demo_mode = True
            return True
        
        try:
            # CPU-only Konfiguration
            os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
            
            # Prüfe Modell-Verfügbarkeit
            if not os.path.exists(self.model_path):
                self.error_handler.log_warning(f"Model file not found: {self.model_path}")
                self.demo_mode = True
                return True
            
            # Datenbank verbinden
            db = SQLDatabase.from_uri(f"sqlite:///{self.db_path}")
            
            # LLM mit modernen Parametern initialisieren
            self.llm = GPT4All(
                model=self.model_path,
                # Entfernte veraltete Parameter: temp, n_ctx, n_gpu_layers
                temperature=0.7,  # Korrekte Parametername
                max_tokens=1024,  # Reduziert für bessere Performance
                n_threads=4,
                verbose=False,
                allow_download=False,
                streaming=False
            )
            
            # Test des LLMs
            test_response = self.llm.invoke("Test")
            self.error_handler.log_info(f"LLM test successful: {test_response[:50]}...")
            
            # Agent erstellen mit moderner API
            self.agent = create_sql_agent(
                llm=self.llm,
                db=db,
                agent_type="zero-shot-react-description",
                verbose=False,
                handle_parsing_errors=True,
                max_execution_time=120
            )
            
            self.initialized = True
            self.error_handler.log_info("Modern LLM Agent successfully initialized")
            return True
            
        except Exception as e:
            self.error_handler.log_error(f"LLM Agent initialization failed: {e}")
            self.demo_mode = True
            return True  # Fallback zu Demo-Modus
    
    def query(self, question: str, timeout: int = 60) -> Dict[str, Any]:
        """Führt eine Abfrage mit modernen APIs aus"""
        start_time = time.time()
        
        try:
            if self.demo_mode or not self.initialized:
                # Demo-Modus mit intelligenten Antworten
                demo_responses = {
                    "aufträge": "Im Demo-Modus: Zeige alle Aufträge mit Status 'Neu' und Region 'Köln'",
                    "status": "Im Demo-Modus: System läuft stabil, Datenbank verbunden",
                    "fehler": "Im Demo-Modus: Keine kritischen Fehler gefunden",
                    "statistik": "Im Demo-Modus: 15 Aufträge heute, 8 abgeschlossen"
                }
                
                # Einfache Schlüsselwort-Erkennung
                question_lower = question.lower()
                for key, response in demo_responses.items():
                    if key in question_lower:
                        return {
                            "success": True,
                            "answer": response,
                            "error": None,
                            "demo_mode": True
                        }
                
                return {
                    "success": True,
                    "answer": f"Demo-Antwort: Ihre Frage '{question}' wurde empfangen. Das System läuft im Demo-Modus ohne KI-Modell.",
                    "error": None,
                    "demo_mode": True
                }
            
            # Echte KI-Verarbeitung
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
                "response_time_ms": response_time,
                "demo_mode": False
            }
            
        except Exception as e:
            response_time = int((time.time() - start_time) * 1000)
            error_msg = str(e)
            self.error_handler.log_error(f"Query failed: {error_msg}")
            
            return {
                "success": False,
                "error": error_msg,
                "answer": f"Fehler bei der Verarbeitung: {error_msg}",
                "response_time_ms": response_time,
                "demo_mode": self.demo_mode
            }

class ErenAssistApp:
    """Hauptanwendung - Version 2025"""
    
    def __init__(self, root):
        self.root = root
        self.version = "2025.1.0"
        self.setup_directories()
        self.setup_error_handling()
        self.setup_components()
        self.setup_gui()
        self.start_background_services()
    
    def setup_directories(self):
        """Erstellt alle notwendigen Verzeichnisse"""
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
        
        # Modell-Konfiguration
        self.MODEL_FILE = "mistral-7b-openorca.Q5_K_M.gguf"
        self.MODEL_PATH = self.MODEL_DIR / self.MODEL_FILE
    
    def setup_error_handling(self):
        """Initialisiert die erweiterte Fehlerbehandlung"""
        log_file = self.LOGS_DIR / f"eren_assist_{time.strftime('%Y%m%d')}.log"
        self.error_handler = ErrorHandler(str(log_file))
        
    def setup_components(self):
        """Initialisiert alle System-Komponenten"""
        self.db_manager = DatabaseManager(str(self.DB_PATH), self.error_handler)
        self.llm_agent = ModernLLMAgent(str(self.MODEL_PATH), str(self.DB_PATH), self.error_handler)
        
        # Threading-Komponenten
        self.stop_event = threading.Event()
        self.question_queue = Queue()
        self.result_queue = Queue()
        
        # System-Status verfolgen
        self.system_status = {
            "database": "unknown",
            "ai_model": "unknown", 
            "ocr": "unknown"
        }
    
    def setup_gui(self):
        """Erstellt die moderne Benutzeroberfläche"""
        self.root.title(f"EREN Assist Enhanced v{self.version}")
        self.root.geometry("1300x900")
        self.root.configure(bg="#f8f9fa")
        
        # Moderne Farben und Styling
        self.colors = {
            "primary": "#3498db",
            "success": "#27ae60", 
            "warning": "#f39c12",
            "danger": "#e74c3c",
            "dark": "#2c3e50",
            "light": "#ecf0f1"
        }
        
        # Header mit verbessertem Design
        header_frame = tk.Frame(self.root, bg=self.colors["dark"], height=100)
        header_frame.pack(fill="x", side="top")
        header_frame.pack_propagate(False)
        
        # Titel und Version
        title_frame = tk.Frame(header_frame, bg=self.colors["dark"])
        title_frame.pack(expand=True, fill="both")
        
        title = tk.Label(title_frame, text="EREN ASSIST Enhanced", 
                        font=("Segoe UI", 22, "bold"), fg="white", bg=self.colors["dark"])
        title.pack(pady=(15, 5))
        
        subtitle = tk.Label(title_frame, text=f"Version {self.version} • Modernisiert für 2025", 
                           font=("Segoe UI", 10), fg="#bdc3c7", bg=self.colors["dark"])
        subtitle.pack()
        
        # Status-Indikatoren mit verbessertem Design
        status_frame = tk.Frame(header_frame, bg=self.colors["dark"])
        status_frame.pack(side="right", padx=20, pady=20)
        
        self.status_indicators = {}
        status_items = [
            ("DB", "database", "🗄️"),
            ("KI", "ai_model", "🤖"), 
            ("OCR", "ocr", "📄")
        ]
        
        for i, (label, key, icon) in enumerate(status_items):
            indicator_frame = tk.Frame(status_frame, bg=self.colors["dark"])
            indicator_frame.grid(row=0, column=i, padx=10)
            
            icon_label = tk.Label(indicator_frame, text=icon, font=("Segoe UI", 16), 
                                 bg=self.colors["dark"], fg="white")
            icon_label.pack()
            
            status_label = tk.Label(indicator_frame, text=f"{label}: ❌", 
                                   font=("Segoe UI", 8), fg="red", bg=self.colors["dark"])
            status_label.pack()
            
            self.status_indicators[key] = status_label
        
        # Hauptbereich mit Notebook-Tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Tab 1: KI-Assistent
        self.setup_ai_tab()
        
        # Tab 2: System-Info
        self.setup_system_tab()
        
        # Tab 3: Verwaltung
        self.setup_management_tab()
        
        # Moderne Statusleiste
        status_frame = tk.Frame(self.root, bg=self.colors["light"], height=30)
        status_frame.pack(side="bottom", fill="x")
        
        self.status_var = tk.StringVar(value="🚀 System wird initialisiert...")
        status_bar = tk.Label(status_frame, textvariable=self.status_var, 
                             font=("Segoe UI", 9), bg=self.colors["light"], 
                             fg=self.colors["dark"], anchor="w")
        status_bar.pack(side="left", fill="x", expand=True, padx=10, pady=5)
        
        # Fortschrittsbalken
        self.progress = ttk.Progressbar(self.root, mode='indeterminate')
    
    def setup_ai_tab(self):
        """Erstellt den modernisierten KI-Assistenten Tab"""
        ai_frame = ttk.Frame(self.notebook)
        self.notebook.add(ai_frame, text="🤖 KI-Assistent")
        
        # Eingabebereich mit modernem Design
        input_container = tk.Frame(ai_frame, bg="white", relief="solid", bd=1)
        input_container.pack(fill="x", padx=10, pady=10)
        
        # Header des Eingabebereichs
        input_header = tk.Frame(input_container, bg=self.colors["primary"], height=40)
        input_header.pack(fill="x")
        input_header.pack_propagate(False)
        
        tk.Label(input_header, text="💬 Stellen Sie Ihre Frage", 
                font=("Segoe UI", 12, "bold"), fg="white", bg=self.colors["primary"]).pack(pady=10)
        
        # Eingabefeld mit Placeholder-Effekt
        input_body = tk.Frame(input_container, bg="white")
        input_body.pack(fill="x", padx=15, pady=15)
        
        self.question_entry = tk.Entry(input_body, font=("Segoe UI", 12), relief="solid", bd=1)
        self.question_entry.pack(fill="x", pady=(0, 10), ipady=8)
        self.question_entry.bind("<Return>", self.ask_question)
        
        # Beispiel-Fragen
        examples_frame = tk.Frame(input_body, bg="white")
        examples_frame.pack(fill="x", pady=(0, 10))
        
        tk.Label(examples_frame, text="💡 Beispiele:", font=("Segoe UI", 9, "bold"), 
                bg="white", fg=self.colors["dark"]).pack(anchor="w")
        
        examples = [
            "Zeige alle Aufträge mit Status 'Neu'",
            "Wie viele Aufträge wurden heute erstellt?", 
            "Welche Regionen haben die meisten offenen Aufträge?"
        ]
        
        for example in examples:
            example_btn = tk.Button(examples_frame, text=f"• {example}", 
                                   font=("Segoe UI", 8), fg=self.colors["primary"],
                                   bg="white", relief="flat", anchor="w",
                                   command=lambda e=example: self.set_example_question(e))
            example_btn.pack(anchor="w", pady=1)
        
        # Buttons mit modernem Design
        button_frame = tk.Frame(input_body, bg="white")
        button_frame.pack(fill="x")
        
        self.ask_button = tk.Button(button_frame, text="🚀 Frage stellen", 
                                   command=self.ask_question, bg=self.colors["primary"], 
                                   fg="white", font=("Segoe UI", 10, "bold"),
                                   relief="flat", padx=20, pady=8)
        self.ask_button.pack(side="left", padx=(0, 10))
        
        clear_btn = tk.Button(button_frame, text="🗑️ Löschen", 
                             command=self.clear_conversation, bg=self.colors["warning"], 
                             fg="white", font=("Segoe UI", 10, "bold"),
                             relief="flat", padx=20, pady=8)
        clear_btn.pack(side="left")
        
        # Antwortbereich mit verbessertem Design
        response_container = tk.Frame(ai_frame, relief="solid", bd=1)
        response_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Header des Antwortbereichs
        response_header = tk.Frame(response_container, bg=self.colors["success"], height=40)
        response_header.pack(fill="x")
        response_header.pack_propagate(False)
        
        tk.Label(response_header, text="💭 Konversation", 
                font=("Segoe UI", 12, "bold"), fg="white", bg=self.colors["success"]).pack(pady=10)
        
        # Antwort-Text mit Syntax-Highlighting
        self.answer_area = scrolledtext.ScrolledText(response_container, wrap="word", 
                                                    font=("Consolas", 10), height=25,
                                                    bg="#fefefe", fg=self.colors["dark"])
        self.answer_area.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Text-Tags für besseres Styling
        self.answer_area.tag_config("timestamp", foreground="#7f8c8d", font=("Segoe UI", 8))
        self.answer_area.tag_config("question", foreground=self.colors["primary"], font=("Segoe UI", 10, "bold"))
        self.answer_area.tag_config("answer", foreground=self.colors["success"], font=("Segoe UI", 10))
        self.answer_area.tag_config("error", foreground=self.colors["danger"], font=("Segoe UI", 10, "bold"))
        self.answer_area.tag_config("demo", foreground=self.colors["warning"], font=("Segoe UI", 10, "italic"))
    
    def setup_system_tab(self):
        """Erstellt den System-Info Tab"""
        system_frame = ttk.Frame(self.notebook)
        self.notebook.add(system_frame, text="📊 System-Info")
        
        # System-Übersicht
        overview_frame = tk.LabelFrame(system_frame, text="🔍 System-Übersicht", 
                                      font=("Segoe UI", 11, "bold"), padx=10, pady=10)
        overview_frame.pack(fill="x", padx=10, pady=10)
        
        self.system_info_text = scrolledtext.ScrolledText(overview_frame, height=8, 
                                                         font=("Consolas", 9))
        self.system_info_text.pack(fill="both", expand=True)
        
        # Performance-Metriken
        metrics_frame = tk.LabelFrame(system_frame, text="⚡ Performance-Metriken", 
                                     font=("Segoe UI", 11, "bold"), padx=10, pady=10)
        metrics_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.metrics_text = scrolledtext.ScrolledText(metrics_frame, height=12, 
                                                     font=("Consolas", 9))
        self.metrics_text.pack(fill="both", expand=True)
    
    def setup_management_tab(self):
        """Erstellt den Verwaltungs-Tab"""
        mgmt_frame = ttk.Frame(self.notebook)
        self.notebook.add(mgmt_frame, text="⚙️ Verwaltung")
        
        # Funktions-Buttons
        functions_frame = tk.LabelFrame(mgmt_frame, text="🛠️ System-Funktionen", 
                                       font=("Segoe UI", 11, "bold"), padx=10, pady=10)
        functions_frame.pack(fill="x", padx=10, pady=10)
        
        buttons_container = tk.Frame(functions_frame)
        buttons_container.pack(fill="x")
        
        buttons = [
            ("📁 PDF-Ordner öffnen", self.open_pdf_folder, self.colors["primary"]),
            ("🔄 System-Check", self.run_system_check, self.colors["success"]),
            ("📊 Datenbank-Info", self.show_database_info, self.colors["warning"]),
            ("🧹 Cache leeren", self.clear_cache, self.colors["danger"])
        ]
        
        for i, (text, command, color) in enumerate(buttons):
            btn = tk.Button(buttons_container, text=text, command=command, 
                           bg=color, fg="white", font=("Segoe UI", 10, "bold"),
                           relief="flat", padx=20, pady=10, width=20)
            btn.grid(row=i//2, column=i%2, padx=10, pady=5, sticky="ew")
        
        buttons_container.columnconfigure(0, weight=1)
        buttons_container.columnconfigure(1, weight=1)
        
        # Log-Bereich
        log_frame = tk.LabelFrame(mgmt_frame, text="📝 System-Logs", 
                                 font=("Segoe UI", 11, "bold"), padx=10, pady=10)
        log_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, font=("Consolas", 9))
        self.log_text.pack(fill="both", expand=True)
    
    def start_background_services(self):
        """Startet alle Hintergrunddienste"""
        # Status-Indikatoren aktualisieren
        self.update_status_indicators()
        
        # LLM-Agent initialisieren
        threading.Thread(target=self.initialize_llm_agent, daemon=True).start()
        
        # Background-Processor
        threading.Thread(target=self.question_processor, daemon=True).start()
        
        # System-Info laden
        threading.Thread(target=self.load_system_info, daemon=True).start()
        
        # Periodische Updates
        self.root.after(5000, self.periodic_updates)
    
    def update_status_indicators(self):
        """Aktualisiert die Status-Indikatoren"""
        # Datenbank-Status
        if self.DB_PATH.exists():
            self.status_indicators["database"].config(text="DB: ✅", fg=self.colors["success"])
            self.system_status["database"] = "connected"
        
        # OCR-Status
        if OCR_AVAILABLE:
            self.status_indicators["ocr"].config(text="OCR: ✅", fg=self.colors["success"])
            self.system_status["ocr"] = "available"
        else:
            self.status_indicators["ocr"].config(text="OCR: ⚠️", fg=self.colors["warning"])
            self.system_status["ocr"] = "unavailable"
    
    def initialize_llm_agent(self):
        """Initialisiert den modernisierten LLM-Agent"""
        self.status_var.set("🤖 Initialisiere KI-Modell...")
        
        try:
            success = self.llm_agent.initialize()
            if success:
                if self.llm_agent.demo_mode:
                    self.status_indicators["ai_model"].config(text="KI: 🔧", fg=self.colors["warning"])
                    self.status_var.set("⚠️ Demo-Modus: KI-Modell nicht gefunden")
                    self.system_status["ai_model"] = "demo_mode"
                else:
                    self.status_indicators["ai_model"].config(text="KI: ✅", fg=self.colors["success"])
                    self.status_var.set("✅ EREN Assist bereit! KI-Modell geladen.")
                    self.system_status["ai_model"] = "ready"
                
                # System-Status in DB loggen
                self.db_manager.log_system_status("ai_model", self.system_status["ai_model"])
                
        except Exception as e:
            self.error_handler.log_error(f"LLM initialization error: {e}")
            self.status_indicators["ai_model"].config(text="KI: ❌", fg=self.colors["danger"])
            self.status_var.set(f"❌ KI-Fehler: {str(e)[:50]}...")
            self.system_status["ai_model"] = "error"
    
    def set_example_question(self, question: str):
        """Setzt eine Beispiel-Frage in das Eingabefeld"""
        self.question_entry.delete(0, tk.END)
        self.question_entry.insert(0, question)
    
    def ask_question(self, event=None):
        """Stellt eine Frage an den modernisierten KI-Agenten"""
        question = self.question_entry.get().strip()
        if not question:
            messagebox.showwarning("Leere Frage", "Bitte geben Sie eine Frage ein.")
            return
        
        self.question_entry.delete(0, tk.END)
        self.question_queue.put(question)
        
        # UI-Feedback
        self.ask_button.config(state="disabled", text="⏳ Verarbeitung...")
        self.status_var.set("⚡ Verarbeite Frage...")
        self.progress.pack(side="bottom", fill="x", before=self.root.children[list(self.root.children.keys())[-1]])
        self.progress.start()
    
    def question_processor(self):
        """Verarbeitet Fragen im Hintergrund mit verbesserter Fehlerbehandlung"""
        while not self.stop_event.is_set():
            try:
                question = self.question_queue.get(timeout=1)
                self.process_single_question(question)
            except Empty:
                continue
            except Exception as e:
                self.error_handler.log_error(f"Question processor error: {e}")
    
    def process_single_question(self, question: str):
        """Verarbeitet eine einzelne Frage mit erweiterten Metriken"""
        start_time = time.time()
        
        try:
            # KI-Abfrage
            result = self.llm_agent.query(question, timeout=120)
            
            # Response-Zeit berechnen
            response_time_ms = int((time.time() - start_time) * 1000)
            
            if result["success"]:
                # Antwort anzeigen
                self.root.after(0, lambda: self.display_answer(
                    question, result["answer"], 
                    demo_mode=result.get("demo_mode", False),
                    response_time_ms=response_time_ms
                ))
                
                # Trainingsdaten speichern
                self.db_manager.save_training_data(
                    question, result["answer"], "Successful query", 
                    None, response_time_ms
                )
            else:
                # Fehler anzeigen
                self.root.after(0, lambda: self.display_error(
                    result["answer"], response_time_ms
                ))
                
                # Fehler-Daten speichern
                self.db_manager.save_training_data(
                    question, None, "Query failed", 
                    result["error"], response_time_ms
                )
                
        except Exception as e:
            response_time_ms = int((time.time() - start_time) * 1000)
            error_msg = f"💥 Unerwarteter Fehler: {str(e)}"
            self.error_handler.log_error(error_msg)
            self.root.after(0, lambda: self.display_error(error_msg, response_time_ms))
        finally:
            # UI-Cleanup
            self.root.after(0, self.cleanup_ui_after_query)
    
    def cleanup_ui_after_query(self):
        """Säubert die UI nach einer Abfrage"""
        self.ask_button.config(state="normal", text="🚀 Frage stellen")
        self.progress.stop()
        self.progress.pack_forget()
        self.status_var.set("✅ Bereit für nächste Frage")
    
    def display_answer(self, question: str, answer: str, demo_mode: bool = False, response_time_ms: int = 0):
        """Zeigt Frage und Antwort mit verbessertem Styling an"""
        self.answer_area.config(state="normal")
        timestamp = time.strftime("%H:%M:%S")
        
        # Zeitstempel
        self.answer_area.insert(tk.END, f"[{timestamp}] ", "timestamp")
        
        # Frage
        self.answer_area.insert(tk.END, f"🙋 FRAGE: {question}\n", "question")
        
        # Antwort mit Demo-Mode Indikator
        if demo_mode:
            self.answer_area.insert(tk.END, f"🤖 DEMO-ANTWORT: {answer}\n", "demo")
        else:
            self.answer_area.insert(tk.END, f"🤖 ANTWORT: {answer}\n", "answer")
        
        # Performance-Info
        self.answer_area.insert(tk.END, f"⚡ Antwortzeit: {response_time_ms}ms\n\n", "timestamp")
        
        self.answer_area.see(tk.END)
        self.answer_area.config(state="disabled")
    
    def display_error(self, error_msg: str, response_time_ms: int = 0):
        """Zeigt eine Fehlermeldung mit Kontext an"""
        self.answer_area.config(state="normal")
        timestamp = time.strftime("%H:%M:%S")
        
        self.answer_area.insert(tk.END, f"[{timestamp}] ", "timestamp")
        self.answer_area.insert(tk.END, f"❌ FEHLER: {error_msg}\n", "error")
        self.answer_area.insert(tk.END, f"⚡ Verarbeitungszeit: {response_time_ms}ms\n\n", "timestamp")
        
        self.answer_area.see(tk.END)
        self.answer_area.config(state="disabled")
    
    def clear_conversation(self):
        """Löscht die Konversation"""
        self.answer_area.config(state="normal")
        self.answer_area.delete(1.0, tk.END)
        self.answer_area.config(state="disabled")
        self.status_var.set("🗑️ Konversation gelöscht")
    
    def load_system_info(self):
        """Lädt detaillierte Systeminformationen"""
        try:
            info_lines = [
                f"EREN ASSIST - SYSTEM-INFORMATION v{self.version}",
                "=" * 60,
                "",
                "📁 VERZEICHNISSE:",
                f"  • Basis: {self.BASE_DIR}",
                f"  • Datenbank: {self.DB_PATH}",
                f"  • PDF-Archiv: {self.PDF_DIR}",
                f"  • KI-Modelle: {self.MODEL_DIR}",
                f"  • Logs: {self.LOGS_DIR}",
                "",
                "🔧 BIBLIOTHEKEN:",
                f"  • LangChain: {'✅ v' + LANGCHAIN_VERSION if LANGCHAIN_AVAILABLE else '❌ Nicht verfügbar'}",
                f"  • OCR (Tesseract): {'✅ Verfügbar' if OCR_AVAILABLE else '❌ Nicht verfügbar'}",
                f"  • PDF (PyMuPDF): {'✅ Verfügbar' if PDF_AVAILABLE else '❌ Nicht verfügbar'}",
                "",
                "⚙️ SYSTEM-STATUS:",
                f"  • Datenbank: {self.system_status['database']}",
                f"  • KI-Modell: {self.system_status['ai_model']}",
                f"  • OCR-System: {self.system_status['ocr']}",
                "",
                "💾 DATEIEN:",
                f"  • KI-Modell existiert: {'✅' if self.MODEL_PATH.exists() else '❌'}",
                f"  • Datenbank existiert: {'✅' if self.DB_PATH.exists() else '❌'}",
                ""
            ]
            
            # PDF-Statistiken
            try:
                pdf_files = list(self.PDF_DIR.glob("*.pdf"))
                info_lines.extend([
                    "📄 PDF-ARCHIV:",
                    f"  • Gesamt PDFs: {len(pdf_files)}",
                    f"  • Gesamtgröße: {self.get_folder_size(self.PDF_DIR):.1f} MB"
                ])
            except Exception as e:
                info_lines.append(f"  • Fehler beim Laden der PDF-Stats: {e}")
            
            info_text = "\n".join(info_lines)
            
            # UI aktualisieren
            self.root.after(0, lambda: self.update_system_info_display(info_text))
            
        except Exception as e:
            self.error_handler.log_error(f"Could not load system info: {e}")
    
    def update_system_info_display(self, info_text: str):
        """Aktualisiert die System-Info-Anzeige"""
        self.system_info_text.delete(1.0, tk.END)
        self.system_info_text.insert(tk.END, info_text)
    
    def get_folder_size(self, folder_path: Path) -> float:
        """Berechnet Ordnergröße in MB"""
        total_size = sum(f.stat().st_size for f in folder_path.rglob('*') if f.is_file())
        return total_size / (1024 * 1024)
    
    def periodic_updates(self):
        """Führt periodische System-Updates durch"""
        try:
            # Performance-Metriken aktualisieren
            self.update_performance_metrics()
            
            # Logs aktualisieren
            self.update_log_display()
            
            # Nächstes Update planen
            self.root.after(30000, self.periodic_updates)  # Alle 30 Sekunden
            
        except Exception as e:
            self.error_handler.log_error(f"Periodic update failed: {e}")
    
    def update_performance_metrics(self):
        """Aktualisiert Performance-Metriken"""
        try:
            # Memory-Usage
            import psutil
            process = psutil.Process(os.getpid())
            memory_mb = process.memory_info().rss / 1024 / 1024
            
            # CPU-Usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Datenbank-Statistiken
            with sqlite3.connect(str(self.DB_PATH)) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM training_log")
                total_queries = cursor.fetchone()[0]
                
                cursor.execute("SELECT AVG(response_time_ms) FROM training_log WHERE response_time_ms IS NOT NULL")
                avg_response_time = cursor.fetchone()[0] or 0
            
            metrics_text = f"""⚡ PERFORMANCE-METRIKEN (Live)
{'=' * 50}

💾 SPEICHER:
  • Aktueller Verbrauch: {memory_mb:.1f} MB
  • System-RAM: {psutil.virtual_memory().percent:.1f}% belegt

🖥️ PROZESSOR:
  • CPU-Auslastung: {cpu_percent:.1f}%
  • Prozessorkerne: {psutil.cpu_count()}

📊 DATENBANK:
  • Gesamt Anfragen: {total_queries}
  • Ø Antwortzeit: {avg_response_time:.0f}ms

🕒 LAUFZEIT:
  • Gestartet: {time.strftime('%H:%M:%S')}
  • Update: {time.strftime('%H:%M:%S')}
"""
            
            self.metrics_text.delete(1.0, tk.END)
            self.metrics_text.insert(tk.END, metrics_text)
            
        except ImportError:
            self.metrics_text.delete(1.0, tk.END)
            self.metrics_text.insert(tk.END, "psutil nicht verfügbar - Installieren Sie es für Performance-Metriken")
        except Exception as e:
            self.error_handler.log_error(f"Metrics update failed: {e}")
    
    def update_log_display(self):
        """Aktualisiert die Log-Anzeige"""
        try:
            log_file = self.LOGS_DIR / f"eren_assist_{time.strftime('%Y%m%d')}.log"
            if log_file.exists():
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    # Zeige nur die letzten 50 Zeilen
                    recent_lines = lines[-50:]
                    log_content = ''.join(recent_lines)
            else:
                log_content = "Keine Logs für heute gefunden."
            
            self.log_text.delete(1.0, tk.END)
            self.log_text.insert(tk.END, log_content)
            self.log_text.see(tk.END)
            
        except Exception as e:
            self.error_handler.log_error(f"Log display update failed: {e}")
    
    def open_pdf_folder(self):
        """Öffnet den PDF-Ordner"""
        try:
            if self.PDF_DIR.exists():
                os.startfile(str(self.PDF_DIR))
                self.status_var.set(f"📁 PDF-Ordner geöffnet: {self.PDF_DIR}")
            else:
                messagebox.showwarning("Ordner nicht gefunden", 
                                     f"PDF-Archiv nicht gefunden: {self.PDF_DIR}")
        except Exception as e:
            self.error_handler.log_error(f"Could not open PDF folder: {e}")
            messagebox.showerror("Fehler", f"Ordner konnte nicht geöffnet werden:\n{str(e)}")
    
    def run_system_check(self):
        """Führt eine umfassende Systemprüfung durch"""
        self.status_var.set("🔍 Führe System-Check durch...")
        threading.Thread(target=self._run_system_check_background, daemon=True).start()
    
    def _run_system_check_background(self):
        """Führt System-Check im Hintergrund durch"""
        try:
            check_results = []
            
            check_results.append("🔍 SYSTEM-CHECK GESTARTET")
            check_results.append("=" * 50)
            check_results.append("")
            
            # Verzeichnisse prüfen
            check_results.append("📁 VERZEICHNISSE:")
            directories = [
                (self.BASE_DIR, "Basisverzeichnis"),
                (self.DB_PATH.parent, "Datenbank-Verzeichnis"),
                (self.PDF_DIR, "PDF-Archiv"),
                (self.MODEL_DIR, "KI-Modelle"),
                (self.LOGS_DIR, "Logs")
            ]
            
            for directory, name in directories:
                status = "✅" if directory.exists() else "❌"
                check_results.append(f"  • {name}: {status}")
            
            check_results.append("")
            
            # Dateien prüfen
            check_results.append("📄 WICHTIGE DATEIEN:")
            files = [
                (self.DB_PATH, "Hauptdatenbank"),
                (self.MODEL_PATH, "KI-Modell")
            ]
            
            for file_path, name in files:
                if file_path.exists():
                    size_mb = file_path.stat().st_size / (1024 * 1024)
                    check_results.append(f"  • {name}: ✅ ({size_mb:.1f} MB)")
                else:
                    check_results.append(f"  • {name}: ❌")
            
            check_results.append("")
            
            # Datenbank-Integrität prüfen
            check_results.append("🗄️ DATENBANK-INTEGRITÄT:")
            try:
                with sqlite3.connect(str(self.DB_PATH)) as conn:
                    cursor = conn.cursor()
                    
                    # Tabellen prüfen
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = cursor.fetchall()
                    check_results.append(f"  • Tabellen gefunden: {len(tables)}")
                    
                    for table_name, in tables:
                        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                        count = cursor.fetchone()[0]
                        check_results.append(f"    - {table_name}: {count} Einträge")
                    
                    check_results.append("  • Datenbank-Status: ✅ Intakt")
                    
            except Exception as e:
                check_results.append(f"  • Datenbank-Fehler: ❌ {str(e)}")
            
            check_results.append("")
            
            # System-Ressourcen prüfen
            try:
                import psutil
                check_results.append("💻 SYSTEM-RESSOURCEN:")
                check_results.append(f"  • RAM verfügbar: {psutil.virtual_memory().available / (1024**3):.1f} GB")
                check_results.append(f"  • CPU-Kerne: {psutil.cpu_count()}")
                check_results.append(f"  • Festplatte frei: {psutil.disk_usage(str(self.BASE_DIR)).free / (1024**3):.1f} GB")
            except ImportError:
                check_results.append("💻 SYSTEM-RESSOURCEN: psutil nicht verfügbar")
            
            check_results.append("")
            check_results.append("✅ SYSTEM-CHECK ABGESCHLOSSEN")
            
            result_text = "\n".join(check_results)
            
            # Ergebnis anzeigen
            self.root.after(0, lambda: self.show_system_check_result(result_text))
            
        except Exception as e:
            error_msg = f"System-Check fehlgeschlagen: {str(e)}"
            self.error_handler.log_error(error_msg)
            self.root.after(0, lambda: messagebox.showerror("System-Check Fehler", error_msg))
    
    def show_system_check_result(self, result_text: str):
        """Zeigt das System-Check Ergebnis an"""
        # Ergebnis in System-Info anzeigen
        self.system_info_text.delete(1.0, tk.END)
        self.system_info_text.insert(tk.END, result_text)
        
        # Wechsle zum System-Info Tab
        self.notebook.select(1)
        
        self.status_var.set("✅ System-Check abgeschlossen")
        messagebox.showinfo("System-Check", "System-Check wurde erfolgreich durchgeführt.\nErgebnisse im System-Info Tab.")
    
    def show_database_info(self):
        """Zeigt detaillierte Datenbank-Informationen"""
        self.status_var.set("📊 Lade Datenbank-Informationen...")
        threading.Thread(target=self._load_database_info_background, daemon=True).start()
    
    def _load_database_info_background(self):
        """Lädt Datenbank-Informationen im Hintergrund"""
        try:
            with sqlite3.connect(str(self.DB_PATH)) as conn:
                cursor = conn.cursor()
                
                info_lines = []
                info_lines.append("📊 DATENBANK-INFORMATION")
                info_lines.append("=" * 50)
                info_lines.append("")
                
                # Tabellen-Übersicht
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                
                info_lines.append(f"📋 TABELLEN ({len(tables)}):")
                info_lines.append("")
                
                for table_name, in tables:
                    # Tabellen-Info
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = cursor.fetchall()
                    
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    row_count = cursor.fetchone()[0]
                    
                    info_lines.append(f"🗂️ {table_name.upper()}:")
                    info_lines.append(f"  • Datensätze: {row_count}")
                    info_lines.append(f"  • Spalten: {len(columns)}")
                    
                    for col in columns[:5]:  # Zeige nur die ersten 5 Spalten
                        info_lines.append(f"    - {col[1]} ({col[2]})")
                    
                    if len(columns) > 5:
                        info_lines.append(f"    ... und {len(columns) - 5} weitere")
                    
                    info_lines.append("")
                
                # Letzte Aktivitäten
                try:
                    cursor.execute("SELECT question, timestamp FROM training_log ORDER BY timestamp DESC LIMIT 5")
                    recent_queries = cursor.fetchall()
                    
                    if recent_queries:
                        info_lines.append("🕒 LETZTE AKTIVITÄTEN:")
                        for question, timestamp in recent_queries:
                            short_question = question[:50] + "..." if len(question) > 50 else question
                            info_lines.append(f"  • {timestamp}: {short_question}")
                        info_lines.append("")
                except:
                    pass
                
                result_text = "\n".join(info_lines)
                
                # UI aktualisieren
                self.root.after(0, lambda: self.update_system_info_display(result_text))
                self.root.after(0, lambda: self.notebook.select(1))
                self.root.after(0, lambda: self.status_var.set("📊 Datenbank-Info geladen"))
                
        except Exception as e:
            error_msg = f"Datenbank-Info Fehler: {str(e)}"
            self.error_handler.log_error(error_msg)
            self.root.after(0, lambda: messagebox.showerror("Datenbank-Fehler", error_msg))
    
    def clear_cache(self):
        """Löscht Cache und temporäre Dateien"""
        result = messagebox.askyesno("Cache löschen", 
            "Dies wird folgende Aktionen durchführen:\n\n"
            "• Temporäre Dateien löschen\n"
            "• Log-Dateien bereinigen (älter als 7 Tage)\n"
            "• System-Cache leeren\n\n"
            "Fortfahren?")
        
        if result:
            threading.Thread(target=self._clear_cache_background, daemon=True).start()
    
    def _clear_cache_background(self):
        """Löscht Cache im Hintergrund"""
        try:
            cleared_items = []
            
            # Temporäre Dateien löschen
            temp_dir = Path(tempfile.gettempdir())
            temp_files = list(temp_dir.glob("eren_temp_*"))
            for temp_file in temp_files:
                try:
                    temp_file.unlink()
                    cleared_items.append(f"Temp-Datei: {temp_file.name}")
                except:
                    pass
            
            # Alte Logs bereinigen (älter als 7 Tage)
            import datetime
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=7)
            
            for log_file in self.LOGS_DIR.glob("eren_assist_*.log"):
                try:
                    file_time = datetime.datetime.fromtimestamp(log_file.stat().st_mtime)
                    if file_time < cutoff_date:
                        log_file.unlink()
                        cleared_items.append(f"Alte Log-Datei: {log_file.name}")
                except:
                    pass
            
            # Ergebnis anzeigen
            if cleared_items:
                result_msg = f"Cache bereinigt!\n\n{len(cleared_items)} Elemente gelöscht:\n"
                result_msg += "\n".join(cleared_items[:10])
                if len(cleared_items) > 10:
                    result_msg += f"\n... und {len(cleared_items) - 10} weitere"
            else:
                result_msg = "Cache bereits sauber!\nKeine zu löschenden Elemente gefunden."
            
            self.root.after(0, lambda: messagebox.showinfo("Cache bereinigt", result_msg))
            self.root.after(0, lambda: self.status_var.set("🧹 Cache erfolgreich bereinigt"))
            
        except Exception as e:
            error_msg = f"Cache-Bereinigung fehlgeschlagen: {str(e)}"
            self.error_handler.log_error(error_msg)
            self.root.after(0, lambda: messagebox.showerror("Cache-Fehler", error_msg))
    
    def on_closing(self):
        """Sauberes Beenden der Anwendung"""
        self.stop_event.set()
        
        # Finale System-Status loggen
        self.db_manager.log_system_status("application", "shutdown", f"Clean shutdown at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Ressourcen freigeben
        if hasattr(self, 'llm_agent') and self.llm_agent.llm:
            try:
                # LLM-Ressourcen freigeben
                del self.llm_agent.llm
            except:
                pass
        
        self.root.destroy()

def main():
    """Hauptfunktion mit erweiterter Fehlerbehandlung"""
    try:
        # Prüfe Python-Version
        if sys.version_info < (3, 8):
            messagebox.showerror("Python-Version", 
                "EREN Assist benötigt Python 3.8 oder höher.\n"
                f"Aktuelle Version: {sys.version_info.major}.{sys.version_info.minor}")
            return
        
        root = tk.Tk()
        app = ErenAssistApp(root)
        
        # Sauberes Beenden sicherstellen
        root.protocol("WM_DELETE_WINDOW", app.on_closing)
        
        # Fenster-Icon (optional)
        try:
            root.iconbitmap('icon.ico')  # Falls vorhanden
        except:
            pass
        
        root.mainloop()
        
    except Exception as e:
        error_msg = f"💥 Kritischer Anwendungsfehler: {str(e)}"
        print(error_msg)
        
        # Versuche GUI-Fehlermeldung anzuzeigen
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("💥 Kritischer Fehler", 
                f"Die Anwendung konnte nicht gestartet werden:\n\n{error_msg}\n\n"
                "Mögliche Lösungen:\n"
                "• Als Administrator ausführen\n"
                "• Python-Installation prüfen\n"
                "• Benötigte Bibliotheken installieren\n"
                "• Antivirensoftware deaktivieren")
            root.destroy()
        except Exception:
            print("GUI konnte nicht gestartet werden. Bitte überprüfen Sie Ihre Tkinter-Installation.")

if __name__ == "__main__":
    main()