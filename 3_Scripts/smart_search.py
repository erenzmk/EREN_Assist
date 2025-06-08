import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
import webbrowser
import os
import hashlib

class SmartSearchInterface:
    """Intelligente Suchoberfläche mit erweiterten Funktionen"""
    
    def __init__(self, root, db_path: str):
        self.root = root
        self.db_path = db_path
        self.search_history = []
        self.current_results = []
        
        self.setup_gui()
        self.load_search_suggestions()
    
    def setup_gui(self):
        """Erstellt die Suchoberfläche"""
        # Hauptframe
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Suchbereich
        search_frame = ttk.LabelFrame(main_frame, text="🔍 Smart Search", padding="10")
        search_frame.pack(fill="x", pady=(0, 10))
        
        # Suchfeld mit Autocomplete
        search_input_frame = ttk.Frame(search_frame)
        search_input_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(search_input_frame, text="Suche:").pack(side="left")
        
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_input_frame, textvariable=self.search_var, font=("Arial", 11))
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(10, 0))
        self.search_entry.bind("<Return>", self.perform_search)
        self.search_entry.bind("<KeyRelease>", self.on_search_input_change)
        
        # Suchoptionen
        options_frame = ttk.Frame(search_frame)
        options_frame.pack(fill="x", pady=(0, 10))
        
        # Dateityp-Filter
        ttk.Label(options_frame, text="Dateityp:").pack(side="left")
        self.filetype_var = tk.StringVar(value="alle")
        filetype_combo = ttk.Combobox(options_frame, textvariable=self.filetype_var, 
                                     values=["alle", "pdf", "word", "image", "text"], state="readonly")
        filetype_combo.pack(side="left", padx=(5, 20))
        
        # Kategorie-Filter
        ttk.Label(options_frame, text="Kategorie:").pack(side="left")
        self.category_var = tk.StringVar(value="alle")
        self.category_combo = ttk.Combobox(options_frame, textvariable=self.category_var, state="readonly")
        self.category_combo.pack(side="left", padx=(5, 20))
        
        # Suchbuttons
        button_frame = ttk.Frame(options_frame)
        button_frame.pack(side="right")
        
        ttk.Button(button_frame, text="Suchen", command=self.perform_search).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Erweitert", command=self.show_advanced_search).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Verlauf", command=self.show_search_history).pack(side="left", padx=5)
        
        # Autocomplete-Dropdown
        self.suggestions_frame = ttk.Frame(search_frame)
        self.suggestions_listbox = tk.Listbox(self.suggestions_frame, height=4)
        self.suggestions_listbox.bind("<Double-Button-1>", self.select_suggestion)
        
        # Ergebnisse-Bereich
        results_frame = ttk.LabelFrame(main_frame, text="📋 Suchergebnisse", padding="10")
        results_frame.pack(fill="both", expand=True)
        
        # Ergebnisse-Toolbar
        toolbar_frame = ttk.Frame(results_frame)
        toolbar_frame.pack(fill="x", pady=(0, 10))
        
        self.results_count_label = ttk.Label(toolbar_frame, text="Keine Ergebnisse")
        self.results_count_label.pack(side="left")
        
        # Sortier-Optionen
        ttk.Label(toolbar_frame, text="Sortieren:").pack(side="right", padx=(20, 5))
        self.sort_var = tk.StringVar(value="relevanz")
        sort_combo = ttk.Combobox(toolbar_frame, textvariable=self.sort_var, 
                                 values=["relevanz", "datum", "name", "größe"], state="readonly", width=12)
        sort_combo.pack(side="right", padx=5)
        sort_combo.bind("<<ComboboxSelected>>", self.resort_results)
        
        # Export-Button
        ttk.Button(toolbar_frame, text="Export", command=self.export_results).pack(side="right", padx=5)
        
        # Ergebnisse-Liste mit Treeview
        columns = ("name", "typ", "relevanz", "größe", "datum", "snippet")
        self.results_tree = ttk.Treeview(results_frame, columns=columns, show="tree headings", height=15)
        
        # Spalten konfigurieren
        self.results_tree.heading("#0", text="📄")
        self.results_tree.column("#0", width=50, anchor="center")
        
        self.results_tree.heading("name", text="Dateiname")
        self.results_tree.column("name", width=200)
        
        self.results_tree.heading("typ", text="Typ")
        self.results_tree.column("typ", width=80, anchor="center")
        
        self.results_tree.heading("relevanz", text="Relevanz")
        self.results_tree.column("relevanz", width=80, anchor="center")
        
        self.results_tree.heading("größe", text="Größe")
        self.results_tree.column("größe", width=80, anchor="center")
        
        self.results_tree.heading("datum", text="Erstellt")
        self.results_tree.column("datum", width=120, anchor="center")
        
        self.results_tree.heading("snippet", text="Vorschau")
        self.results_tree.column("snippet", width=400)
        
        # Scrollbar für Ergebnisse
        scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=scrollbar.set)
        
        self.results_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Doppelklick-Binding
        self.results_tree.bind("<Double-1>", self.open_result)
        