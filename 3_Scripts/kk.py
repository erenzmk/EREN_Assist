import warnings
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
    """Zentrale Fehlerbehandlung mit verschiedenen Schweregrade"""
    
    def __init__(self, log_file: str):
        self.log_file = log_file
        self.setup_logging()
        
    def setup_logging(self):
        """Konfiguriert das Logging-System"""
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

class SafeFileHandler:
    """Sichere Dateioperationen mit Retry-Mechanismus"""
    
    @staticmethod
    def safe_delete_file(file_path: str, max_retries: int = 5, delay: float = 0.5) -> bool:
        """Löscht Dateien sicher mit Wiederholungen"""
        if not os.path.exists(file_path):
            return True
            
        for attempt in range(max_retries):
            try:
                os.unlink(file_path)
                return True
            except PermissionError:
                if attempt < max_retries - 1:
                    time.sleep(delay * (2 ** attempt))  # Exponential backoff
                continue
            except Exception as e:
                logging.error(f"Unexpected error deleting {file_path}: {e}")
                return False
        
        logging.error(f"Could not delete file after {max_retries} attempts: {file_path}")
        return False
    
    @staticmethod
    def safe_create_temp_file(prefix: str = "eren_temp_", suffix: str = ".png") -> Optional[str]:
        """Erstellt temporäre Dateien sicher"""
        try:
            temp_fd, temp_path = tempfile.mkstemp(prefix=prefix, suffix=suffix)
            os.close(temp_fd)  # Schließe File Descriptor sofort
            return temp_path
        except Exception as e:
            logging.error(f"Could not create temp file: {e}")
            return None

class DatabaseManager:
    """Verbesserte Datenbankoperationen mit Fehlerbehandlung"""
    
    def __init__(self, db_path: str, error_handler: ErrorHandler):
        self.db_path = db_path
        self.error_handler = error_handler
        self.ensure_database_exists()
    
    def ensure_database_exists(self):
        """Stellt sicher, dass die Datenbank existiert"""
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
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS error_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        error_type TEXT,
                        error_message TEXT,
                        context TEXT
                    )
                """)
                conn.commit()
        except sqlite3.Error as e:
            self.error_handler.log_error(f"Database creation failed: {e}")
    
    def save_training_data(self, question: str, answer: Optional[str], 
                          thinking_process: str, error_info: Optional[str] = None):
        """Speichert Trainingsdaten sicher"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO training_log (question, answer, thinking_process, error_info)
                    VALUES (?, ?, ?, ?)
                """, (question, answer, thinking_process, error_info))
                conn.commit()
        except sqlite3.Error as e:
            self.error_handler.log_error(f"Failed to save training data: {e}")
    
    def log_error_to_db(self, error_type: str, error_message: str, context: str = ""):
        """Speichert Fehler in der Datenbank"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO error_log (error_type, error_message, context)
                    VALUES (?, ?, ?)
                """, (error_type, error_message, context))
                conn.commit()
        except sqlite3.Error as e:
            self.error_handler.log_error(f"Failed to log error to database: {e}")

class ImprovedOCRProcessor:
    """Verbesserte OCR-Verarbeitung mit besserer Fehlerbehandlung"""
    
    def __init__(self, tesseract_path: str, error_handler: ErrorHandler):
        self.tesseract_path = tesseract_path
        self.error_handler = error_handler
        self.setup_tesseract()
    
    def setup_tesseract(self):
        """Konfiguriert Tesseract"""
        if OCR_AVAILABLE and os.path.exists(self.tesseract_path):
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_path
            self.error_handler.log_info("Tesseract successfully configured")
        else:
            self.error_handler.log_warning("Tesseract not available or not found")
    
    def process_pdf_page(self, page, page_num: int) -> Optional[str]:
        """Verarbeitet eine einzelne PDF-Seite mit OCR"""
        if not OCR_AVAILABLE or not PDF_AVAILABLE:
            self.error_handler.log_error("Required libraries not available for OCR")
            return None
        
        temp_img_path = None
        try:
            # Erstelle temporäre Datei
            temp_img_path = SafeFileHandler.safe_create_temp_file(
                prefix=f"eren_page_{page_num}_", suffix=".png"
            )
            if not temp_img_path:
                return None
            
            # Rendere Seite als Bild
            matrix = fitz.Matrix(2.0, 2.0)  # 2x Vergrößerung für bessere OCR
            pix = page.get_pixmap(matrix=matrix)
            pix.save(temp_img_path)
            
            # OCR durchführen
            with Image.open(temp_img_path) as img:
                text = pytesseract.image_to_string(
                    img, 
                    lang='deu+eng',
                    config='--oem 3 --psm 6'  # Optimierte OCR-Parameter
                )
            
            return text.strip()
            
        except Exception as e:
            self.error_handler.log_error(f"OCR processing failed for page {page_num}: {e}")
            return None
        finally:
            if temp_img_path and os.path.exists(temp_img_path):
                SafeFileHandler.safe_delete_file(temp_img_path)
    
    def create_searchable_pdf(self, input_pdf: str, output_pdf: str) -> bool:
        """Erstellt durchsuchbares PDF mit verbesserter Fehlerbehandlung"""
        if not PDF_AVAILABLE:
            self.error_handler.log_error("PyMuPDF not available")
            return False
        
        doc = None
        new_doc = None
        
        try:
            doc = fitz.open(input_pdf)
            new_doc = fitz.open()
            
            for page_num in range(len(doc)):
                try:
                    page = doc.load_page(page_num)
                    
                    # OCR für diese Seite durchführen
                    text = self.process_pdf_page(page, page_num)
                    
                    # Neue Seite erstellen
                    new_page = new_doc.new_page(
                        width=page.rect.width, 
                        height=page.rect.height
                    )
                    
                    # Original-Seite als Bild einfügen
                    pix = page.get_pixmap(matrix=fitz.Matrix(1.0, 1.0))
                    temp_img_path = SafeFileHandler.safe_create_temp_file()
                    if temp_img_path:
                        pix.save(temp_img_path)
                        new_page.insert_image(new_page.rect, filename=temp_img_path)
                        SafeFileHandler.safe_delete_file(temp_img_path)
                    
                    # Text hinzufügen (falls OCR erfolgreich)
                    if text:
                        try:
                            new_page.insert_textbox(
                                new_page.rect,
                                text,
                                fontname="helv",
                                fontsize=8,
                                color=(1, 1, 1),  # Weiß (unsichtbar)
                                fill=None
                            )
                        except Exception as e:
                            self.error_handler.log_warning(f"Could not insert text for page {page_num}: {e}")
                    
                except Exception as e:
                    self.error_handler.log_error(f"Failed to process page {page_num}: {e}")
                    continue
            
            # Speichere das neue PDF
            new_doc.save(output_pdf)
            return True
            
        except Exception as e:
            self.error_handler.log_error(f"PDF OCR creation failed: {e}")
            return False
        finally:
            if new_doc:
                new_doc.close()
            if doc:
                doc.close()

class RobustLLMAgent:
    """Robuster LLM-Agent mit verbesserter Fehlerbehandlung"""
    
    def __init__(self, model_path: str, db_path: str, error_handler: ErrorHandler):
        self.model_path = model_path
        self.db_path = db_path
        self.error_handler = error_handler
        self.agent = None
        self.initialized = False
    
    def initialize(self) -> bool:
        """Initialisiert den LLM-Agent"""
        if not LANGCHAIN_AVAILABLE:
            self.error_handler.log_error("LangChain not available")
            return False
        
        try:
            # Umgebungsvariablen für CPU-only setzen
            os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
            os.environ["GGML_CUDA_OVERRIDE"] = "0"
            
            # Datenbank verbinden
            db = SQLDatabase.from_uri(f"sqlite:///{self.db_path}")
            
            # LLM initialisieren
            llm = GPT4All(
                model=self.model_path,
                verbose=False,
                device='cpu',
                n_threads=4,
                temp=0.3,
                max_tokens=1024,
                allow_download=False
            )
            
            # Agent erstellen
            self.agent = create_sql_agent(
                llm=llm,
                db=db,
                agent_type="zero-shot-react-description",
                verbose=False,
                max_execution_time=120,
                max_iterations=10
            )
            
            self.initialized = True
            self.error_handler.log_info("LLM Agent successfully initialized")
            return True
            
        except Exception as e:
            self.error_handler.log_error(f"LLM Agent initialization failed: {e}")
            return False
    
    def query(self, question: str, timeout: int = 60) -> Dict[str, Any]:
        """Führt eine Abfrage mit Timeout aus"""
        if not self.initialized:
            return {
                "success": False,
                "error": "Agent not initialized",
                "answer": "Agent ist nicht initialisiert"
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
        """Erstellt alle notwendigen Verzeichnisse"""
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
        self.TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    
    def setup_error_handling(self):
        """Initialisiert die Fehlerbehandlung"""
        log_file = self.BASE_DIR / "eren_assist_error.log"
        self.error_handler = ErrorHandler(str(log_file))
        
    def setup_components(self):
        """Initialisiert alle Komponenten"""
        self.db_manager = DatabaseManager(str(self.DB_PATH), self.error_handler)
        self.ocr_processor = ImprovedOCRProcessor(self.TESSERACT_PATH, self.error_handler)
        self.llm_agent = RobustLLMAgent(str(self.MODEL_PATH), str(self.DB_PATH), self.error_handler)
        
        # Threading-Komponenten
        self.stop_event = threading.Event()
        self.question_queue = Queue()
        self.result_queue = Queue()
        self.thinking_queue = Queue()
        
    def setup_gui(self):
        """Erstellt die Benutzeroberfläche"""
        self.root.title("EREN Assist - Robuste KI-gestützte Datenanalyse")
        self.root.geometry("1200x800")
        self.root.configure(bg="#f0f2f5")
        
        # Header
        header_frame = tk.Frame(self.root, bg="#2c3e50", height=80)
        header_frame.pack(fill="x", side="top")
        
        title = tk.Label(header_frame, text="EREN ASSIST (Verbessert)", 
                        font=("Arial", 20, "bold"), fg="white", bg="#2c3e50")
        title.pack(pady=15)
        
        # Status-Indikatoren
        status_frame = tk.Frame(header_frame, bg="#2c3e50")
        status_frame.pack(side="right", padx=20)
        
        self.db_status = tk.Label(status_frame, text="DB: ❌", fg="red", bg="#2c3e50")
        self.db_status.pack(side="left", padx=5)
        
        self.ocr_status = tk.Label(status_frame, text="OCR: ❌", fg="red", bg="#2c3e50")
        self.ocr_status.pack(side="left", padx=5)
        
        self.model_status = tk.Label(status_frame, text="KI: ❌", fg="red", bg="#2c3e50")
        self.model_status.pack(side="left", padx=5)
        
        # Hauptbereich mit Tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Tab 1: KI-Assistent
        self.setup_ai_tab(notebook)
        
        # Tab 2: Verwaltung
        self.setup_management_tab(notebook)
        
        # Tab 3: Fehlerprotokoll
        self.setup_error_tab(notebook)
        
        # Statusleiste
        self.status_var = tk.StringVar(value="System wird initialisiert...")
        status_bar = tk.Label(self.root, textvariable=self.status_var, 
                             bd=1, relief="sunken", anchor="w", bg="#ecf0f1")
        status_bar.pack(side="bottom", fill="x")
        
        # Fortschrittsbalken
        self.progress = ttk.Progressbar(self.root, mode='indeterminate')
    
    def setup_ai_tab(self, notebook):
        """Erstellt den KI-Assistenten Tab"""
        ai_frame = ttk.Frame(notebook)
        notebook.add(ai_frame, text="KI-Assistent")
        
        # Eingabebereich
        input_frame = tk.Frame(ai_frame, bg="white", relief="groove", bd=2)
        input_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Label(input_frame, text="Ihre Frage:", bg="white", font=("Arial", 11, "bold")).pack(anchor="w", padx=10, pady=5)
        
        self.question_entry = tk.Entry(input_frame, font=("Arial", 11))
        self.question_entry.pack(fill="x", padx=10, pady=5)
        self.question_entry.bind("<Return>", self.ask_question)
        
        button_frame = tk.Frame(input_frame, bg="white")
        button_frame.pack(pady=10)
        
        ask_btn = tk.Button(button_frame, text="Frage stellen", command=self.ask_question,
                           bg="#3498db", fg="white", font=("Arial", 10, "bold"))
        ask_btn.pack(side="left", padx=5)
        
        clear_btn = tk.Button(button_frame, text="Löschen", command=self.clear_conversation,
                             bg="#95a5a6", fg="white", font=("Arial", 10, "bold"))
        clear_btn.pack(side="left", padx=5)
        
        # Zwei-Spalten Layout für Denkprozess und Antwort
        content_frame = tk.Frame(ai_frame)
        content_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Linke Spalte - Denkprozess
        thinking_frame = tk.Frame(content_frame, relief="groove", bd=2)
        thinking_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        tk.Label(thinking_frame, text="Denkprozess der KI:", font=("Arial", 11, "bold")).pack(anchor="w", padx=5, pady=5)
        self.thinking_area = scrolledtext.ScrolledText(thinking_frame, wrap="word", 
                                                      font=("Consolas", 9), height=15)
        self.thinking_area.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Rechte Spalte - Antworten
        answer_frame = tk.Frame(content_frame, relief="groove", bd=2)
        answer_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        tk.Label(answer_frame, text="Antworten:", font=("Arial", 11, "bold")).pack(anchor="w", padx=5, pady=5)
        self.answer_area = scrolledtext.ScrolledText(answer_frame, wrap="word", 
                                                    font=("Arial", 10), height=15)
        self.answer_area.pack(fill="both", expand=True, padx=5, pady=5)
    
    def setup_management_tab(self, notebook):
        """Erstellt den Verwaltungs-Tab"""
        mgmt_frame = ttk.Frame(notebook)
        notebook.add(mgmt_frame, text="Verwaltung")
        
        # Funktionsbuttons
        btn_frame = tk.Frame(mgmt_frame)
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        buttons = [
            ("PDF-Ordner öffnen", self.open_pdf_folder, "#3498db"),
            ("OCR durchführen", self.run_ocr_batch, "#16a085"),
            ("Datenbank anzeigen", self.show_database, "#9b59b6"),
            ("System prüfen", self.system_check, "#e67e22"),
            ("Notfall-Reset", self.emergency_reset, "#e74c3c")
        ]
        
        for i, (text, command, color) in enumerate(buttons):
            btn = tk.Button(btn_frame, text=text, command=command, bg=color, fg="white",
                           font=("Arial", 10, "bold"), width=20, height=2)
            btn.grid(row=i//3, column=i%3, padx=5, pady=5)
        
        # Informationsbereich
        info_frame = tk.Frame(mgmt_frame, relief="groove", bd=2)
        info_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        tk.Label(info_frame, text="System-Information:", font=("Arial", 11, "bold")).pack(anchor="w", padx=5, pady=5)
        self.info_area = scrolledtext.ScrolledText(info_frame, wrap="word", 
                                                  font=("Consolas", 9), height=10)
        self.info_area.pack(fill="both", expand=True, padx=5, pady=5)
    
    def setup_error_tab(self, notebook):
        """Erstellt den Fehlerprotokoll-Tab"""
        error_frame = ttk.Frame(notebook)
        notebook.add(error_frame, text="Fehlerprotokoll")
        
        # Kontrollen
        control_frame = tk.Frame(error_frame)
        control_frame.pack(fill="x", padx=10, pady=5)
        
        refresh_btn = tk.Button(control_frame, text="Aktualisieren", 
                               command=self.refresh_error_log, bg="#3498db", fg="white")
        refresh_btn.pack(side="left", padx=5)
        
        clear_log_btn = tk.Button(control_frame, text="Log löschen", 
                                 command=self.clear_error_log, bg="#e74c3c", fg="white")
        clear_log_btn.pack(side="left", padx=5)
        
        # Fehlerprotokoll
        self.error_log_area = scrolledtext.ScrolledText(error_frame, wrap="word", 
                                                       font=("Consolas", 9))
        self.error_log_area.pack(fill="both", expand=True, padx=10, pady=5)
    
    def start_background_services(self):
        """Startet Hintergrunddienste"""
        # Status aktualisieren
        self.update_status_indicators()
        
        # LLM-Agent initialisieren
        if self.MODEL_PATH.exists():
            threading.Thread(target=self.initialize_llm_agent, daemon=True).start()
        else:
            self.status_var.set("Modell nicht gefunden - bitte herunterladen")
        
        # Überwachungs-Threads
        threading.Thread(target=self.question_processor, daemon=True).start()
        threading.Thread(target=self.thinking_updater, daemon=True).start()
        
        # Initiale Systeminformationen laden
        threading.Thread(target=self.load_system_info, daemon=True).start()
    
    def update_status_indicators(self):
        """Aktualisiert die Status-Indikatoren"""
        # Datenbank-Status
        if self.DB_PATH.exists():
            self.db_status.config(text="DB: ✔", fg="green")
        
        # OCR-Status
        if OCR_AVAILABLE and os.path.exists(self.TESSERACT_PATH):
            self.ocr_status.config(text="OCR: ✔", fg="green")
        elif OCR_AVAILABLE:
            self.ocr_status.config(text="OCR: ⚠", fg="orange")
        
        # Modell-Status wird später aktualisiert
    
    def initialize_llm_agent(self):
        """Initialisiert den LLM-Agent"""
        self.status_var.set("Initialisiere KI-Modell...")
        self.thinking_queue.put("Starte KI-Modell-Initialisierung...")
        
        try:
            success = self.llm_agent.initialize()
            if success:
                self.model_status.config(text="KI: ✔", fg="green")
                self.status_var.set("KI-Agent bereit!")
                self.thinking_queue.put("KI-Agent erfolgreich initialisiert!")
            else:
                self.model_status.config(text="KI: ❌", fg="red")
                self.status_var.set("KI-Agent-Initialisierung fehlgeschlagen")
                self.thinking_queue.put("KI-Agent-Initialisierung fehlgeschlagen!")
        except Exception as e:
            self.error_handler.log_error(f"LLM initialization error: {e}")
            self.model_status.config(text="KI: ❌", fg="red")
            self.status_var.set(f"Fehler: {str(e)}")
    
    def ask_question(self, event=None):
        """Stellt eine Frage an den KI-Agenten"""
        question = self.question_entry.get().strip()
        if not question:
            return
        
        if not self.llm_agent.initialized:
            messagebox.showwarning("Nicht bereit", "KI-Agent ist noch nicht bereit!")
            return
        
        self.question_entry.delete(0, "end")
        self.question_queue.put(question)
        
        # Visuelles Feedback
        self.status_var.set("Verarbeite Frage...")
        self.progress.pack(side="bottom", fill="x")
        self.progress.start()
    
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
        thinking_log = []
        
        try:
            # Denkprozess dokumentieren
            thinking_log.append(f"Verarbeite Frage: '{question}'")
            self.thinking_queue.put(thinking_log[-1])
            
            thinking_log.append("Analysiere Frage und suche relevante Daten...")
            self.thinking_queue.put(thinking_log[-1])
            
            # KI-Abfrage
            result = self.llm_agent.query(question, timeout=120)
            
            if result["success"]:
                thinking_log.append("Antwort erfolgreich generiert")
                self.thinking_queue.put(thinking_log[-1])
                
                # Antwort anzeigen
                self.root.after(0, lambda: self.display_answer(question, result["answer"]))
                
                # Trainingsdaten speichern
                self.db_manager.save_training_data(
                    question, result["answer"], "\n".join(thinking_log)
                )
            else:
                thinking_log.append(f"Fehler: {result['error']}")
                self.thinking_queue.put(thinking_log[-1])
                
                # Fehler anzeigen
                self.root.after(0, lambda: self.display_error(result["answer"]))
                
                # Fehler in Trainingsdaten speichern
                self.db_manager.save_training_data(
                    question, None, "\n".join(thinking_log), result["error"]
                )
            
        except Exception as e:
            error_msg = f"Unerwarteter Fehler: {str(e)}"
            thinking_log.append(error_msg)
            self.thinking_queue.put(error_msg)
            self.error_handler.log_error(error_msg)
            self.root.after(0, lambda: self.display_error(error_msg))
        finally:
            # UI-Cleanup
            self.root.after(0, self.progress.stop)
            self.root.after(0, self.progress.pack_forget)
            self.root.after(0, lambda: self.status_var.set("Bereit"))
    
    def thinking_updater(self):
        """Aktualisiert den Denkprozess-Bereich"""
        while not self.stop_event.is_set():
            try:
                thought = self.thinking_queue.get(timeout=0.5)
                self.root.after(0, lambda t=thought: self.update_thinking_display(t))
            except Empty:
                continue
    
    def update_thinking_display(self, text: str):
        """Aktualisiert die Denkprozess-Anzeige"""
        self.thinking_area.config(state="normal")
        timestamp = time.strftime("%H:%M:%S")
        self.thinking_area.insert(tk.END, f"[{timestamp}] {text}\n")
        self.thinking_area.see(tk.END)
        self.thinking_area.config(state="disabled")
    
    def display_answer(self, question: str, answer: str):
        """Zeigt Frage und Antwort an"""
        self.answer_area.config(state="normal")
        timestamp = time.strftime("%H:%M:%S")
        
        self.answer_area.insert(tk.END, f"\n[{timestamp}] FRAGE: {question}\n", "question")
        self.answer_area.insert(tk.END, f"ANTWORT: {answer}\n\n", "answer")
        self.answer_area.see(tk.END)
        self.answer_area.config(state="disabled")
        
        # Text-Tags für Styling
        self.answer_area.tag_config("question", foreground="blue", font=("Arial", 10, "bold"))
        self.answer_area.tag_config("answer", foreground="darkgreen")
    
    def display_error(self, error_msg: str):
        """Zeigt eine Fehlermeldung an"""
        self.answer_area.config(state="normal")
        timestamp = time.strftime("%H:%M:%S")
        self.answer_area.insert(tk.END, f"\n[{timestamp}] FEHLER: {error_msg}\n\n", "error")
        self.answer_area.see(tk.END)
        self.answer_area.config(state="disabled")
        
        self.answer_area.tag_config("error", foreground="red", font=("Arial", 10, "bold"))
    
    def clear_conversation(self):
        """Löscht die Konversation"""
        self.answer_area.config(state="normal")
        self.answer_area.delete(1.0, tk.END)
        self.answer_area.config(state="disabled")
        
        self.thinking_area.config(state="normal")
        self.thinking_area.delete(1.0, tk.END)
        self.thinking_area.config(state="disabled")
    
    def open_pdf_folder(self):
        """Öffnet den PDF-Ordner"""
        try:
            if self.PDF_DIR.exists():
                os.startfile(str(self.PDF_DIR))
                self.status_var.set(f"PDF-Ordner geöffnet: {self.PDF_DIR}")
            else:
                messagebox.showwarning("Ordner nicht gefunden", 
                                     f"PDF-Archiv nicht gefunden: {self.PDF_DIR}")
        except Exception as e:
            self.error_handler.log_error(f"Could not open PDF folder: {e}")
            messagebox.showerror("Fehler", f"Ordner konnte nicht geöffnet werden:\n{str(e)}")
    
    def run_ocr_batch(self):
        """Startet Batch-OCR für alle PDFs"""
        if not OCR_AVAILABLE:
            messagebox.showerror("OCR nicht verfügbar", 
                               "OCR-Bibliotheken sind nicht installiert!")
            return
        
        if not os.path.exists(self.TESSERACT_PATH):
            messagebox.showerror("Tesseract nicht gefunden", 
                               f"Tesseract wurde nicht gefunden: {self.TESSERACT_PATH}")
            return
        
        self.status_var.set("Starte OCR-Batch-Verarbeitung...")
        threading.Thread(target=self.process_ocr_batch, daemon=True).start()
    
    def process_ocr_batch(self):
        """Verarbeitet alle PDFs mit OCR"""
        try:
            pdf_files = list(self.PDF_DIR.glob("*.pdf"))
            if not pdf_files:
                self.root.after(0, lambda: messagebox.showinfo("Keine PDFs", 
                    "Keine PDF-Dateien im Archiv gefunden"))
                return
            
            processed = 0
            errors = 0
            
            for pdf_file in pdf_files:
                if "_ocr" in pdf_file.name:
                    continue  # Bereits verarbeitet
                
                self.status_var.set(f"OCR: {pdf_file.name} ({processed+1}/{len(pdf_files)})")
                
                output_path = pdf_file.with_name(pdf_file.stem + "_ocr.pdf")
                
                if self.ocr_processor.create_searchable_pdf(str(pdf_file), str(output_path)):
                    # Ersetze Original mit OCR-Version
                    try:
                        pdf_file.unlink()
                        output_path.rename(pdf_file)
                        processed += 1
                        self.thinking_queue.put(f"OCR erfolgreich: {pdf_file.name}")
                    except Exception as e:
                        self.error_handler.log_error(f"Could not replace original PDF: {e}")
                        errors += 1
                else:
                    errors += 1
                    self.thinking_queue.put(f"OCR fehlgeschlagen: {pdf_file.name}")
            
            # Ergebnis anzeigen
            result_msg = f"OCR abgeschlossen: {processed} erfolgreich, {errors} Fehler"
            self.status_var.set(result_msg)
            self.root.after(0, lambda: messagebox.showinfo("OCR Abgeschlossen", result_msg))
            
        except Exception as e:
            error_msg = f"OCR-Batch fehlgeschlagen: {str(e)}"
            self.error_handler.log_error(error_msg)
            self.root.after(0, lambda: messagebox.showerror("Fehler", error_msg))
    
    def show_database(self):
        """Zeigt Datenbankinhalt an"""
        self.info_area.delete(1.0, tk.END)
        self.info_area.insert(tk.END, "Lade Datenbankstruktur...\n")
        threading.Thread(target=self.load_database_info, daemon=True).start()
    
    def load_database_info(self):
        """Lädt Datenbankinformationen"""
        try:
            with sqlite3.connect(str(self.DB_PATH)) as conn:
                cursor = conn.cursor()
                
                # Tabellen auflisten
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                
                info_text = "=== DATENBANKSTRUKTUR ===\n\n"
                
                for table_name, in tables:
                    info_text += f"TABELLE: {table_name}\n"
                    
                    # Spalteninformationen
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = cursor.fetchall()
                    
                    info_text += "Spalten:\n"
                    for col in columns:
                        info_text += f"  - {col[1]} ({col[2]})\n"
                    
                    # Anzahl Datensätze
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cursor.fetchone()[0]
                    info_text += f"Datensätze: {count}\n"
                    
                    # Beispieldaten
                    if count > 0:
                        cursor.execute(f"SELECT * FROM {table_name} LIMIT 2")
                        rows = cursor.fetchall()
                        info_text += "Beispieldaten:\n"
                        for row in rows:
                            short_row = [str(item)[:50] + "..." if len(str(item)) > 50 
                                       else str(item) for item in row]
                            info_text += f"  {short_row}\n"
                    
                    info_text += "\n" + "-"*50 + "\n\n"
                
                # UI aktualisieren
                self.root.after(0, lambda: self.update_info_area(info_text))
                
        except Exception as e:
            error_msg = f"Datenbankfehler: {str(e)}"
            self.error_handler.log_error(error_msg)
            self.root.after(0, lambda: self.update_info_area(error_msg))
    
    def update_info_area(self, text: str):
        """Aktualisiert den Info-Bereich"""
        self.info_area.delete(1.0, tk.END)
        self.info_area.insert(tk.END, text)
        self.info_area.see(1.0)
    
    def system_check(self):
        """Führt eine Systemprüfung durch"""
        self.info_area.delete(1.0, tk.END)
        self.info_area.insert(tk.END, "Führe Systemprüfung durch...\n")
        threading.Thread(target=self.run_system_check, daemon=True).start()
    
    def run_system_check(self):
        """Führt umfassende Systemprüfung durch"""
        check_results = []
        
        # Bibliotheken prüfen
        check_results.append("=== BIBLIOTHEKS-STATUS ===")
        check_results.append(f"LangChain verfügbar: {'✓' if LANGCHAIN_AVAILABLE else '✗'}")
        check_results.append(f"OCR verfügbar: {'✓' if OCR_AVAILABLE else '✗'}")
        check_results.append(f"PDF verfügbar: {'✓' if PDF_AVAILABLE else '✗'}")
        
        # Dateisystem prüfen
        check_results.append("\n=== DATEISYSTEM ===")
        check_results.append(f"Basisverzeichnis: {'✓' if self.BASE_DIR.exists() else '✗'}")
        check_results.append(f"Datenbank: {'✓' if self.DB_PATH.exists() else '✗'}")
        check_results.append(f"PDF-Archiv: {'✓' if self.PDF_DIR.exists() else '✗'}")
        check_results.append(f"KI-Modell: {'✓' if self.MODEL_PATH.exists() else '✗'}")
        check_results.append(f"Tesseract: {'✓' if os.path.exists(self.TESSERACT_PATH) else '✗'}")
        
        # Datenbank prüfen
        check_results.append("\n=== DATENBANK ===")
        try:
            with sqlite3.connect(str(self.DB_PATH)) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM training_log")
                training_count = cursor.fetchone()[0]
                check_results.append(f"Trainingsdaten: {training_count} Einträge")
                
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                table_count = len(cursor.fetchall())
                check_results.append(f"Tabellen: {table_count}")
        except Exception as e:
            check_results.append(f"Datenbankfehler: {str(e)}")
        
        # KI-Status prüfen
        check_results.append("\n=== KI-SYSTEM ===")
        check_results.append(f"Agent initialisiert: {'✓' if self.llm_agent.initialized else '✗'}")
        
        # PDF-Archiv prüfen
        check_results.append("\n=== PDF-ARCHIV ===")
        try:
            pdf_files = list(self.PDF_DIR.glob("*.pdf"))
            check_results.append(f"PDF-Dateien: {len(pdf_files)}")
            
            ocr_files = [f for f in pdf_files if "_ocr" in f.name]
            check_results.append(f"OCR-verarbeitet: {len(ocr_files)}")
        except Exception as e:
            check_results.append(f"PDF-Archiv-Fehler: {str(e)}")
        
        # Speicherplatz prüfen
        check_results.append("\n=== SPEICHERPLATZ ===")
        try:
            import shutil
            total, used, free = shutil.disk_usage(str(self.BASE_DIR))
            check_results.append(f"Verfügbar: {free // (1024**3)} GB")
            check_results.append(f"Gesamt: {total // (1024**3)} GB")
        except Exception as e:
            check_results.append(f"Speicherplatz-Fehler: {str(e)}")
        
        result_text = "\n".join(check_results)
        self.root.after(0, lambda: self.update_info_area(result_text))
    
    def emergency_reset(self):
        """Führt einen Notfall-Reset durch"""
        result = messagebox.askyesno(
            "Notfall-Reset", 
            "WARNUNG: Dies wird folgende Aktionen durchführen:\n\n"
            "• Alle Trainingsdaten löschen\n"
            "• Fehlerprotokolle zurücksetzen\n"
            "• KI-Agent neu initialisieren\n"
            "• Temporäre Dateien bereinigen\n\n"
            "Möchten Sie fortfahren?"
        )
        
        if not result:
            return
        
        threading.Thread(target=self.perform_emergency_reset, daemon=True).start()
    
    def perform_emergency_reset(self):
        """Führt den eigentlichen Reset durch"""
        try:
            self.status_var.set("Führe Notfall-Reset durch...")
            reset_steps = []
            
            # 1. Trainingsdaten löschen
            try:
                with sqlite3.connect(str(self.DB_PATH)) as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM training_log")
                    cursor.execute("DELETE FROM error_log")
                    conn.commit()
                reset_steps.append("✓ Trainingsdaten gelöscht")
            except Exception as e:
                reset_steps.append(f"✗ Trainingsdaten: {str(e)}")
            
            # 2. Log-Dateien löschen
            try:
                log_file = self.BASE_DIR / "eren_assist_error.log"
                if log_file.exists():
                    log_file.unlink()
                reset_steps.append("✓ Log-Dateien gelöscht")
            except Exception as e:
                reset_steps.append(f"✗ Log-Dateien: {str(e)}")
            
            # 3. Temporäre Dateien bereinigen
            try:
                temp_dir = Path(tempfile.gettempdir())
                temp_files = list(temp_dir.glob("eren_temp_*"))
                for temp_file in temp_files:
                    SafeFileHandler.safe_delete_file(str(temp_file))
                reset_steps.append(f"✓ {len(temp_files)} temporäre Dateien gelöscht")
            except Exception as e:
                reset_steps.append(f"✗ Temp-Dateien: {str(e)}")
            
            # 4. KI-Agent neu initialisieren
            try:
                self.llm_agent.initialized = False
                self.model_status.config(text="KI: ❌", fg="red")
                threading.Thread(target=self.initialize_llm_agent, daemon=True).start()
                reset_steps.append("✓ KI-Agent wird neu initialisiert")
            except Exception as e:
                reset_steps.append(f"✗ KI-Agent: {str(e)}")
            
            # Ergebnis anzeigen
            result_text = "NOTFALL-RESET ABGESCHLOSSEN\n\n" + "\n".join(reset_steps)
            self.root.after(0, lambda: self.update_info_area(result_text))
            self.root.after(0, lambda: messagebox.showinfo("Reset abgeschlossen", 
                "Der Notfall-Reset wurde durchgeführt.\nDas System sollte jetzt wieder funktionieren."))
            
        except Exception as e:
            error_msg = f"Reset fehlgeschlagen: {str(e)}"
            self.error_handler.log_error(error_msg)
            self.root.after(0, lambda: messagebox.showerror("Reset-Fehler", error_msg))
    
    def load_system_info(self):
        """Lädt Systeminformationen"""
        try:
            info_text = f"""EREN ASSIST - SYSTEMINFORMATIONEN

Verzeichnisse:
• Basis: {self.BASE_DIR}
• Datenbank: {self.DB_PATH}
• PDFs: {self.PDF_DIR}
• Modelle: {self.MODEL_DIR}

Bibliotheken:
• LangChain: {'Verfügbar' if LANGCHAIN_AVAILABLE else 'Nicht verfügbar'}
• OCR (Tesseract/PIL): {'Verfügbar' if OCR_AVAILABLE else 'Nicht verfügbar'}
• PDF (PyMuPDF): {'Verfügbar' if PDF_AVAILABLE else 'Nicht verfügbar'}

Status:
• KI-Modell: {'Bereit' if self.llm_agent.initialized else 'Wird initialisiert...'}
• Datenbank: {'Verbunden' if self.DB_PATH.exists() else 'Nicht gefunden'}

Hinweis: Nutzen Sie die Systemprüfung für detaillierte Informationen.
"""
            self.root.after(0, lambda: self.update_info_area(info_text))
        except Exception as e:
            self.error_handler.log_error(f"Could not load system info: {e}")
    
    def refresh_error_log(self):
        """Aktualisiert das Fehlerprotokoll"""
        try:
            log_file = self.BASE_DIR / "eren_assist_error.log"
            if log_file.exists():
                with open(log_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Zeige nur die letzten 1000 Zeilen
                    lines = content.split('\n')
                    if len(lines) > 1000:
                        content = '\n'.join(lines[-1000:])
                        content = "... (ältere Einträge ausgeblendet) ...\n\n" + content
            else:
                content = "Keine Fehlerprotokolle gefunden."
            
            self.error_log_area.delete(1.0, tk.END)
            self.error_log_area.insert(tk.END, content)
            self.error_log_area.see(tk.END)
            
        except Exception as e:
            self.error_log_area.delete(1.0, tk.END)
            self.error_log_area.insert(tk.END, f"Fehler beim Laden des Logs: {str(e)}")
    
    def clear_error_log(self):
        """Löscht das Fehlerprotokoll"""
        result = messagebox.askyesno("Log löschen", 
            "Möchten Sie das Fehlerprotokoll wirklich löschen?")
        if result:
            try:
                log_file = self.BASE_DIR / "eren_assist_error.log"
                if log_file.exists():
                    log_file.unlink()
                self.error_log_area.delete(1.0, tk.END)
                self.error_log_area.insert(tk.END, "Fehlerprotokoll gelöscht.")
                messagebox.showinfo("Erfolg", "Fehlerprotokoll wurde gelöscht.")
            except Exception as e:
                messagebox.showerror("Fehler", f"Log konnte nicht gelöscht werden: {str(e)}")
    
    def on_closing(self):
        """Sauberes Beenden der Anwendung"""
        self.stop_event.set()
        
        # Ressourcen freigeben
        if hasattr(self.llm_agent, 'agent') and self.llm_agent.agent:
            try:
                if hasattr(self.llm_agent.agent, 'llm') and hasattr(self.llm_agent.agent.llm, 'client'):
                    self.llm_agent.agent.llm.client.close()
            except Exception:
                pass
        
        # Temporäre Dateien bereinigen
        try:
            temp_dir = Path(tempfile.gettempdir())
            temp_files = list(temp_dir.glob("eren_temp_*"))
            for temp_file in temp_files:
                SafeFileHandler.safe_delete_file(str(temp_file))
        except Exception:
            pass
        
        self.root.destroy()

def main():
    """Hauptfunktion mit Fehlerbehandlung"""
    try:
        root = tk.Tk()
        app = ErenAssistApp(root)
        
        # Sauberes Beenden sicherstellen
        root.protocol("WM_DELETE_WINDOW", app.on_closing)
        
        # Stile konfigurieren
        root.option_add("*Font", "Arial 10")
        
        root.mainloop()
        
    except Exception as e:
        error_msg = f"Kritischer Anwendungsfehler: {str(e)}"
        print(error_msg)
        
        # Versuche GUI-Fehlermeldung anzuzeigen
        try:
            root = tk.Tk()
            root.withdraw()  # Verstecke Hauptfenster
            messagebox.showerror("Kritischer Fehler", 
                f"Die Anwendung konnte nicht gestartet werden:\n\n{error_msg}\n\n"
                "Bitte überprüfen Sie:\n"
                "• Python-Installation\n"
                "• Erforderliche Bibliotheken\n"
                "• Dateiberechtigungen\n"
                "• Verfügbarer Speicherplatz")
            root.destroy()
        except Exception:
            # Fallback auf Konsolen-Ausgabe
            print("GUI konnte nicht gestartet werden. Bitte überprüfen Sie Ihre Tkinter-Installation.")

if __name__ == "__main__":
    main()