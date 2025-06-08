import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import seaborn as sns
from typing import Dict, List, Any
import threading

class AnalyticsDashboard:
    """Analytics Dashboard für EREN Assist mit Diagrammen und Metriken"""
    
    def __init__(self, root, db_path: str):
        self.root = root
        self.db_path = db_path
        self.analytics_db = str(Path(db_path).parent / "eren_analytics.db")
        
        self.setup_gui()
        self.load_dashboard_data()
    
    def setup_gui(self):
        """Erstellt das Dashboard-Interface"""
        # Hauptframe
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill="x", pady=(0, 20))
        
        ttk.Label(header_frame, text="📊 EREN Assist Analytics Dashboard", 
                 font=("Arial", 16, "bold")).pack(side="left")
        
        # Refresh Button
        ttk.Button(header_frame, text="🔄 Aktualisieren", 
                  command=self.refresh_dashboard).pack(side="right")
        
        # Auto-Refresh Checkbox
        self.auto_refresh_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(header_frame, text="Auto-Refresh (5min)", 
                       variable=self.auto_refresh_var).pack(side="right", padx=(0, 10))
        
        # Notebook für verschiedene Analytics-Bereiche
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill="both", expand=True)
        
        # Tab 1: Übersicht
        self.setup_overview_tab()
        
        # Tab 2: Auftragsverfolgung
        self.setup_orders_tab()
        
        # Tab 3: KI-Performance
        self.setup_ai_performance_tab()
        
        # Tab 4: Dateien & OCR
        self.setup_files_ocr_tab()
        
        # Tab 5: Suchstatistiken
        self.setup_search_stats_tab()
        
        # Auto-Refresh starten
        self.start_auto_refresh()
    
    def setup_overview_tab(self):
        """Erstellt den Übersichts-Tab"""
        overview_frame = ttk.Frame(self.notebook)
        self.notebook.add(overview_frame, text="📈 Übersicht")
        
        # KPI-Karten oben
        kpi_frame = ttk.Frame(overview_frame)
        kpi_frame.pack(fill="x", padx=10, pady=10)
        
        # KPI-Karten (4 Spalten)
        self.kpi_cards = {}
        kpi_data = [
            ("Aktive Aufträge", "0", "📋", "#3498db"),
            ("Heute verarbeitet", "0", "✅", "#2ecc71"), 
            ("KI-Anfragen (24h)", "0", "🤖", "#9b59b6"),
            ("Ø Antwortzeit", "0ms", "⚡", "#e74c3c")
        ]
        
        for i, (title, value, icon, color) in enumerate(kpi_data):
            card_frame = tk.Frame(kpi_frame, bg=color, relief="raised", bd=2)
            card_frame.grid(row=0, column=i, padx=10, pady=5, sticky="ew")
            
            tk.Label(card_frame, text=icon, font=("Arial", 20), bg=color, fg="white").pack(pady=(10, 0))
            value_label = tk.Label(card_frame, text=value, font=("Arial", 16, "bold"), bg=color, fg="white")
            value_label.pack()
            tk.Label(card_frame, text=title, font=("Arial", 10), bg=color, fg="white").pack(pady=(0, 10))
            
            self.kpi_cards[title] = value_label
        
        # Grid-Gewichtung für gleichmäßige Verteilung
        for i in range(4):
            kpi_frame.columnconfigure(i, weight=1)
        
        # Charts-Bereich
        charts_frame = ttk.Frame(overview_frame)
        charts_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Linkes Chart - Aufträge über Zeit
        left_chart_frame = ttk.LabelFrame(charts_frame, text="📈 Aufträge letzte 30 Tage", padding="10")
        left_chart_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        self.overview_fig, self.overview_axes = plt.subplots(1, 2, figsize=(12, 4))
        self.overview_canvas = FigureCanvasTkAgg(self.overview_fig, left_chart_frame)
        self.overview_canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # Rechtes Chart - System Health
        right_chart_frame = ttk.LabelFrame(charts_frame, text="🔧 System Status", padding="10")
        right_chart_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        # System Health Indikatoren
        health_items = [
            ("Datenbank", "🟢", "Optimal"),
            ("OCR-Service", "🟢", "Läuft"),
            ("KI-Agent", "🟢", "Bereit"),
            ("Backup-System", "🟢", "Aktiv"),
            ("Speicherplatz", "🟡", "75% belegt"),
            ("Netzwerk", "🟢", "Verbunden")
        ]
        
        for item, status, desc in health_items:
            health_row = ttk.Frame(right_chart_frame)
            health_row.pack(fill="x", pady=2)
            
            ttk.Label(health_row, text=item, width=15).pack(side="left")
            ttk.Label(health_row, text=status).pack(side="left", padx=(10, 5))
            ttk.Label(health_row, text=desc, foreground="gray").pack(side="left")
    
    def setup_orders_tab(self):
        """Erstellt den Auftrags-Tab"""
        orders_frame = ttk.Frame(self.notebook)
        self.notebook.add(orders_frame, text="📋 Aufträge")
        
        # Filter-Bereich
        filter_frame = ttk.LabelFrame(orders_frame, text="🔍 Filter & Optionen", padding="10")
        filter_frame.pack(fill="x", padx=10, pady=10)
        
        # Zeitraum-Filter
        ttk.Label(filter_frame, text="Zeitraum:").grid(row=0, column=0, sticky="w", padx=(0, 5))
        self.time_range_var = tk.StringVar(value="30_tage")
        time_range_combo = ttk.Combobox(filter_frame, textvariable=self.time_range_var,
                                       values=["7_tage", "30_tage", "90_tage", "1_jahr"], state="readonly")
        time_range_combo.grid(row=0, column=1, padx=5)
        
        # Status-Filter  
        ttk.Label(filter_frame, text="Status:").grid(row=0, column=2, sticky="w", padx=(20, 5))
        self.status_filter_var = tk.StringVar(value="alle")
        status_combo = ttk.Combobox(filter_frame, textvariable=self.status_filter_var,
                                   values=["alle", "neu", "in_bearbeitung", "erledigt"], state="readonly")
        status_combo.grid(row=0, column=3, padx=5)
        
        # Region-Filter
        ttk.Label(filter_frame, text="Region:").grid(row=0, column=4, sticky="w", padx=(20, 5))
        self.region_filter_var = tk.StringVar(value="alle")
        self.region_combo = ttk.Combobox(filter_frame, textvariable=self.region_filter_var, state="readonly")
        self.region_combo.grid(row=0, column=5, padx=5)
        
        # Update Button
        ttk.Button(filter_frame, text="🔄 Aktualisieren", 
                  command=self.update_orders_data).grid(row=0, column=6, padx=(20, 0))
        
        # Charts für Aufträge
        orders_charts_frame = ttk.Frame(orders_frame)
        orders_charts_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Chart 1: Aufträge nach Status (Pie Chart)
        status_chart_frame = ttk.LabelFrame(orders_charts_frame, text="📊 Aufträge nach Status", padding="10")
        status_chart_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        self.orders_fig, self.orders_axes = plt.subplots(2, 2, figsize=(12, 8))
        self.orders_canvas = FigureCanvasTkAgg(self.orders_fig, status_chart_frame)
        self.orders_canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # Tabelle für Top-Probleme
        table_frame = ttk.LabelFrame(orders_charts_frame, text="🚨 Häufigste Probleme", padding="10")
        table_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        # Treeview für Top-Probleme
        columns = ("problem", "anzahl", "trend")
        self.problems_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=12)
        
        self.problems_tree.heading("problem", text="Problem/Fehlercode")
        self.problems_tree.heading("anzahl", text="Anzahl")
        self.problems_tree.heading("trend", text="Trend")
        
        self.problems_tree.column("problem", width=200)
        self.problems_tree.column("anzahl", width=80, anchor="center")
        self.problems_tree.column("trend", width=80, anchor="center")
        
        problems_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.problems_tree.yview)
        self.problems_tree.configure(yscrollcommand=problems_scroll.set)
        
        self.problems_tree.pack(side="left", fill="both", expand=True)
        problems_scroll.pack(side="right", fill="y")
    
    def setup_ai_performance_tab(self):
        """Erstellt den KI-Performance Tab"""
        ai_frame = ttk.Frame(self.notebook)
        self.notebook.add(ai_frame, text="🤖 KI-Performance")
        
        # KI-Metriken oben
        ai_metrics_frame = ttk.LabelFrame(ai_frame, text="⚡ KI-Leistungsmetriken", padding="10")
        ai_metrics_frame.pack(fill="x", padx=10, pady=10)
        
        # Metriken-Grid
        metrics_data = [
            ("Durchschn. Antwortzeit", "0ms", "⚡"),
            ("Erfolgsrate", "0%", "✅"),
            ("Anfragen heute", "0", "📊"),
            ("Modell-Uptime", "0h", "⏱️")
        ]
        
        self.ai_metrics = {}
        for i, (title, value, icon) in enumerate(metrics_data):
            metric_frame = ttk.Frame(ai_metrics_frame)
            metric_frame.grid(row=0, column=i, padx=20, pady=10, sticky="ew")
            
            ttk.Label(metric_frame, text=icon, font=("Arial", 16)).pack()
            value_label = ttk.Label(metric_frame, text=value, font=("Arial", 14, "bold"))
            value_label.pack()
            ttk.Label(metric_frame, text=title, font=("Arial", 10)).pack()
            
            self.ai_metrics[title] = value_label
        
        for i in range(4):
            ai_metrics_frame.columnconfigure(i, weight=1)
        
        # KI-Charts
        ai_charts_frame = ttk.Frame(ai_frame)
        ai_charts_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Performance über Zeit
        perf_chart_frame = ttk.LabelFrame(ai_charts_frame, text="📈 Performance-Trends", padding="10")
        perf_chart_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        self.ai_fig, self.ai_axes = plt.subplots(2, 1, figsize=(8, 8))
        self.ai_canvas = FigureCanvasTkAgg(self.ai_fig, perf_chart_frame)
        self.ai_canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # Top-Queries Tabelle
        queries_frame = ttk.LabelFrame(ai_charts_frame, text="🔍 Häufigste Anfragen", padding="10")
        queries_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        # Treeview für Top-Queries
        query_columns = ("query", "count", "avg_time", "success_rate")
        self.queries_tree = ttk.Treeview(queries_frame, columns=query_columns, show="headings", height=15)
        
        self.queries_tree.heading("query", text="Anfrage")
        self.queries_tree.heading("count", text="Anzahl")
        self.queries_tree.heading("avg_time", text="Ø Zeit")
        self.queries_tree.heading("success_rate", text="Erfolg")
        
        self.queries_tree.column("query", width=250)
        self.queries_tree.column("count", width=60, anchor="center")
        self.queries_tree.column("avg_time", width=80, anchor="center")
        self.queries_tree.column("success_rate", width=80, anchor="center")
        
        queries_scroll = ttk.Scrollbar(queries_frame, orient="vertical", command=self.queries_tree.yview)
        self.queries_tree.configure(yscrollcommand=queries_scroll.set)
        
        self.queries_tree.pack(side="left", fill="both", expand=True)
        queries_scroll.pack(side="right", fill="y")
    
    def setup_files_ocr_tab(self):
        """Erstellt den Dateien & OCR Tab"""
        files_frame = ttk.Frame(self.notebook)
        self.notebook.add(files_frame, text="📄 Dateien & OCR")
        
        # Datei-Statistiken
        file_stats_frame = ttk.LabelFrame(files_frame, text="📊 Datei-Statistiken", padding="10")
        file_stats_frame.pack(fill="x", padx=10, pady=10)
        
        stats_data = [
            ("Gesamt Dateien", "0", "📁"),
            ("OCR verarbeitet", "0", "🔍"),
            ("Durchschn. OCR-Qualität", "0%", "✨"),
            ("Gesamt-Speicher", "0 MB", "💾")
        ]
        
        self.file_stats = {}
        for i, (title, value, icon) in enumerate(stats_data):
            stat_frame = ttk.Frame(file_stats_frame)
            stat_frame.grid(row=0, column=i, padx=20, pady=10, sticky="ew")
            
            ttk.Label(stat_frame, text=icon, font=("Arial", 16)).pack()
            value_label = ttk.Label(stat_frame, text=value, font=("Arial", 14, "bold"))
            value_label.pack()
            ttk.Label(stat_frame, text=title, font=("Arial", 10)).pack()
            
            self.file_stats[title] = value_label
        
        for i in range(4):
            file_stats_frame.columnconfigure(i, weight=1)
        
        # Datei-Charts
        files_charts_frame = ttk.Frame(files_frame)
        files_charts_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Charts für Dateitypen und OCR-Qualität
        chart_frame = ttk.LabelFrame(files_charts_frame, text="📊 Datei-Analyse", padding="10")
        chart_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        self.files_fig, self.files_axes = plt.subplots(2, 2, figsize=(10, 8))
        self.files_canvas = FigureCanvasTkAgg(self.files_fig, chart_frame)
        self.files_canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # OCR-Probleme Tabelle
        ocr_problems_frame = ttk.LabelFrame(files_charts_frame, text="⚠️ OCR-Probleme", padding="10")
        ocr_problems_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        # Treeview für OCR-Probleme
        ocr_columns = ("file", "error", "confidence", "status")
        self.ocr_tree = ttk.Treeview(ocr_problems_frame, columns=ocr_columns, show="headings", height=15)
        
        self.ocr_tree.heading("file", text="Datei")
        self.ocr_tree.heading("error", text="Fehler")
        self.ocr_tree.heading("confidence", text="Vertrauen")
        self.ocr_tree.heading("status", text="Status")
        
        self.ocr_tree.column("file", width=150)
        self.ocr_tree.column("error", width=200)
        self.ocr_tree.column("confidence", width=80, anchor="center")
        self.ocr_tree.column("status", width=80, anchor="center")
        
        ocr_scroll = ttk.Scrollbar(ocr_problems_frame, orient="vertical", command=self.ocr_tree.yview)
        self.ocr_tree.configure(yscrollcommand=ocr_scroll.set)
        
        self.ocr_tree.pack(side="left", fill="both", expand=True)
        ocr_scroll.pack(side="right", fill="y")
    
    def setup_search_stats_tab(self):
        """Erstellt den Suchstatistiken Tab"""
        search_frame = ttk.Frame(self.notebook)
        self.notebook.add(search_frame, text="🔍 Suchstatistiken")
        
        # Such-Metriken
        search_metrics_frame = ttk.LabelFrame(search_frame, text="📈 Such-Metriken", padding="10")
        search_metrics_frame.pack(fill="x", padx=10, pady=10)
        
        search_data = [
            ("Suchen heute", "0", "🔍"),
            ("Ø Suchzeit", "0ms", "⚡"),
            ("Erfolgsrate", "0%", "✅"),
            ("Unique Queries", "0", "📝")
        ]
        
        self.search_stats = {}
        for i, (title, value, icon) in enumerate(search_data):
            stat_frame = ttk.Frame(search_metrics_frame)
            stat_frame.grid(row=0, column=i, padx=20, pady=10, sticky="ew")
            
            ttk.Label(stat_frame, text=icon, font=("Arial", 16)).pack()
            value_label = ttk.Label(stat_frame, text=value, font=("Arial", 14, "bold"))
            value_label.pack()
            ttk.Label(stat_frame, text=title, font=("Arial", 10)).pack()
            
            self.search_stats[title] = value_label
        
        for i in range(4):
            search_metrics_frame.columnconfigure(i, weight=1)
        
        # Such-Charts und Wordcloud
        search_charts_frame = ttk.Frame(search_frame)
        search_charts_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Search Trends Chart
        trends_frame = ttk.LabelFrame(search_charts_frame, text="📊 Such-Trends", padding="10")
        trends_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        self.search_fig, self.search_axes = plt.subplots(2, 1, figsize=(8, 8))
        self.search_canvas = FigureCanvasTkAgg(self.search_fig, trends_frame)
        self.search_canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # Top Search Terms
        terms_frame = ttk.LabelFrame(search_charts_frame, text="🏆 Top Suchbegriffe", padding="10")
        terms_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        terms_columns = ("term", "count", "success_rate", "avg_time")
        self.terms_tree = ttk.Treeview(terms_frame, columns=terms_columns, show="headings", height=15)
        
        self.terms_tree.heading("term", text="Suchbegriff")
        self.terms_tree.heading("count", text="Anzahl")
        self.terms_tree.heading("success_rate", text="Erfolg")
        self.terms_tree.heading("avg_time", text="Ø Zeit")
        
        self.terms_tree.column("term", width=200)
        self.terms_tree.column("count", width=60, anchor="center")
        self.terms_tree.column("success_rate", width=80, anchor="center")
        self.terms_tree.column("avg_time", width=80, anchor="center")
        
        terms_scroll = ttk.Scrollbar(terms_frame, orient="vertical", command=self.terms_tree.yview)
        self.terms_tree.configure(yscrollcommand=terms_scroll.set)
        
        self.terms_tree.pack(side="left", fill="both", expand=True)
        terms_scroll.pack(side="right", fill="y")
    
    def load_dashboard_data(self):
        """Lädt alle Dashboard-Daten"""
        threading.Thread(target=self._load_data_background, daemon=True).start()
    
    def _load_data_background(self):
        """Lädt Daten im Hintergrund"""
        try:
            self.load_overview_data()
            self.load_orders_data()
            self.load_ai_performance_data()
            self.load_files_ocr_data()
            self.load_search_stats_data()
        except Exception as e:
            print(f"Fehler beim Laden der Dashboard-Daten: {e}")
    
    def load_overview_data(self):
        """Lädt Übersichtsdaten"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # KPI-Daten laden
                # Aktive Aufträge
                cursor.execute("SELECT COUNT(*) FROM auftraege_enhanced WHERE status != 'erledigt'")
                active_orders = cursor.fetchone()[0]
                self.root.after(0, lambda: self.kpi_cards["Aktive Aufträge"].config(text=str(active_orders)))
                
                # Heute verarbeitet
                today = datetime.now().strftime("%Y-%m-%d")
                cursor.execute("SELECT COUNT(*) FROM auftraege_enhanced WHERE DATE(aktualisiert_am) = ?", (today,))
                today_processed = cursor.fetchone()[0]
                self.root.after(0, lambda: self.kpi_cards["Heute verarbeitet"].config(text=str(today_processed)))
                
                # KI-Anfragen 24h
                yesterday = datetime.now() - timedelta(days=1)
                cursor.execute("SELECT COUNT(*) FROM ki_interaktionen WHERE erstellt_am > ?", (yesterday,))
                ai_queries_24h = cursor.fetchone()[0]
                self.root.after(0, lambda: self.kpi_cards["KI-Anfragen (24h)"].config(text=str(ai_queries_24h)))
                
                # Durchschnittliche Antwortzeit
                cursor.execute("SELECT AVG(verarbeitungszeit_ms) FROM ki_interaktionen WHERE erstellt_am > ?", (yesterday,))
                avg_response = cursor.fetchone()[0] or 0
                self.root.after(0, lambda: self.kpi_cards["Ø Antwortzeit"].config(text=f"{avg_response:.0f}ms"))
                
        except sqlite3.Error as e:
            print(f"Fehler beim Laden der Übersichtsdaten: {e}")
    
    def load_orders_data(self):
        """Lädt Auftragsdaten"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Regionen für Filter laden
                cursor.execute("SELECT DISTINCT region FROM auftraege_enhanced WHERE region IS NOT NULL")
                regions = ["alle"] + [row[0] for row in cursor.fetchall()]
                self.root.after(0, lambda: self.region_combo.configure(values=regions))
                
        except sqlite3.Error as e:
            print(f"Fehler beim Laden der Auftragsdaten: {e}")
    
    def load_ai_performance_data(self):
        """Lädt KI-Performance-Daten"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # KI-Metriken berechnen
                yesterday = datetime.now() - timedelta(days=1)
                
                # Durchschnittliche Antwortzeit
                cursor.execute("SELECT AVG(verarbeitungszeit_ms) FROM ki_interaktionen WHERE erstellt_am > ?", (yesterday,))
                avg_time = cursor.fetchone()[0] or 0
                self.root.after(0, lambda: self.ai_metrics["Durchschn. Antwortzeit"].config(text=f"{avg_time:.0f}ms"))
                
        except sqlite3.Error as e:
            print(f"Fehler beim Laden der KI-Performance-Daten: {e}")
    
    def load_files_ocr_data(self):
        """Lädt Dateien & OCR-Daten"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Datei-Statistiken
                cursor.execute("SELECT COUNT(*) FROM datei_metadaten")
                total_files = cursor.fetchone()[0]
                self.root.after(0, lambda: self.file_stats["Gesamt Dateien"].config(text=str(total_files)))
                
        except sqlite3.Error as e:
            print(f"Fehler beim Laden der Datei-OCR-Daten: {e}")
    
    def load_search_stats_data(self):
        """Lädt Suchstatistiken-Daten"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Such-Metriken
                today = datetime.now().strftime("%Y-%m-%d")
                cursor.execute("SELECT COUNT(*) FROM query_analytics WHERE DATE(letzte_verwendung) = ?", (today,))
                searches_today = cursor.fetchone()[0]
                self.root.after(0, lambda: self.search_stats["Suchen heute"].config(text=str(searches_today)))
                
        except sqlite3.Error as e:
            print(f"Fehler beim Laden der Suchstatistiken: {e}")
    
    def update_orders_data(self):
        """Aktualisiert Auftragsdaten basierend auf Filtern"""
        threading.Thread(target=self.load_orders_data, daemon=True).start()
    
    def refresh_dashboard(self):
        """Aktualisiert das gesamte Dashboard"""
        threading.Thread(target=self._load_data_background, daemon=True).start()
    
    def start_auto_refresh(self):
        """Startet automatisches Refresh alle 5 Minuten"""
        def auto_refresh():
            if self.auto_refresh_var.get():
                self.refresh_dashboard()
            self.root.after(300000, auto_refresh)  # 5 Minuten = 300000ms
        
        self.root.after(300000, auto_refresh)

# Standalone-Anwendung für Analytics Dashboard
def main():
    """Startet das Analytics Dashboard als eigenständige Anwendung"""
    import sys
    import os
    
    root = tk.Tk()
    root.title("EREN Assist - Analytics Dashboard")
    root.geometry("1400x900")
    
    # Datenbankpfad
    db_path = r"C:\EREN_Assist\1_Datenbank\eren_assist.db"
    
    if not os.path.exists(db_path):
        messagebox.showerror("Fehler", f"Datenbank nicht gefunden: {db_path}")
        sys.exit(1)
    
    # Matplotlib-Backend konfigurieren
    plt.style.use('default')
    
    # Analytics Dashboard erstellen
    dashboard = AnalyticsDashboard(root, db_path)
    
    root.mainloop()

if __name__ == "__main__":
    main()