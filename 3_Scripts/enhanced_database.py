import sqlite3
import os
import json
import time
import hashlib
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import logging

class EnhancedDatabaseEngine:
    """Erweiterte Datenbank-Engine mit Performance-Optimierungen und Features"""
    
    def __init__(self, base_dir: str = r"C:\EREN_Assist"):
        self.base_dir = Path(base_dir)
        self.db_dir = self.base_dir / "1_Datenbank"
        self.backup_dir = self.base_dir / "BACKUPS"
        self.main_db = self.db_dir / "eren_assist.db"
        self.analytics_db = self.db_dir / "eren_analytics.db"
        
        # Erstelle Verzeichnisse
        self.db_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Logging konfigurieren
        self.setup_logging()
        
        # Datenbanken initialisieren
        self.init_enhanced_schema()
        self.init_analytics_schema()
        
    def setup_logging(self):
        """Konfiguriert erweiterte Logging-Funktionen"""
        log_file = self.base_dir / "database_performance.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def init_enhanced_schema(self):
        """Erstellt erweiterte Datenbankstruktur mit Indizes"""
        with sqlite3.connect(self.main_db) as conn:
            cursor = conn.cursor()
            
            # 1. Erweiterte Aufträge-Tabelle
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS auftraege_enhanced (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    auftragsnummer TEXT UNIQUE NOT NULL,
                    region TEXT,
                    beschreibung TEXT,
                    fehlercode TEXT,
                    festnetznummer TEXT,
                    status TEXT DEFAULT 'Neu',
                    prioritaet INTEGER DEFAULT 3,
                    erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    aktualisiert_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    zugewiesen_an TEXT,
                    geschaetzt_dauer INTEGER,
                    tatsaechliche_dauer INTEGER,
                    kundenbewertung INTEGER,
                    notizen TEXT,
                    tags TEXT,
                    gps_koordinaten TEXT,
                    server_anmeldung INTEGER DEFAULT 0
                )
            ''')
            
            # 2. Erweiterte Datei-Metadaten
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS datei_metadaten (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    datei_name TEXT NOT NULL,
                    originaler_name TEXT,
                    dateipfad TEXT,
                    typ TEXT,
                    groesse_bytes INTEGER,
                    erstellt_am TIMESTAMP,
                    geaendert_am TIMESTAMP,
                    hash_md5 TEXT,
                    hash_sha256 TEXT,
                    verarbeitet_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ocr_status TEXT DEFAULT 'pending',
                    ocr_vertrauen REAL,
                    sprache_erkannt TEXT,
                    seiten_anzahl INTEGER,
                    wort_anzahl INTEGER,
                    zeichen_anzahl INTEGER,
                    inhalt_preview TEXT,
                    volltext_inhalt TEXT,
                    kategorien TEXT,
                    schlagwoerter TEXT
                )
            ''')
            
            # 3. OCR-Ergebnisse mit Details
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ocr_ergebnisse (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    datei_id INTEGER,
                    seiten_nummer INTEGER,
                    text_inhalt TEXT,
                    vertrauen_score REAL,
                    sprache TEXT,
                    verarbeitet_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    verarbeitungszeit_ms INTEGER,
                    erkannte_woerter INTEGER,
                    fehler_info TEXT,
                    bounding_boxes TEXT,
                    FOREIGN KEY (datei_id) REFERENCES datei_metadaten(id)
                )
            ''')
            
            # 4. Erweiterte Abkürzungen mit Kontext
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS abkuerzungen_enhanced (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT UNIQUE NOT NULL,
                    bedeutung TEXT NOT NULL,
                    kategorie TEXT,
                    beschreibung TEXT,
                    synonyme TEXT,
                    verwendung_haeufigkeit INTEGER DEFAULT 0,
                    pdf_referenzen TEXT,
                    erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    aktualisiert_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    validiert_durch TEXT,
                    status TEXT DEFAULT 'aktiv'
                )
            ''')
            
            # 5. KI-Interaktionen mit Performance-Metriken
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ki_interaktionen (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sitzung_id TEXT,
                    frage TEXT NOT NULL,
                    antwort TEXT,
                    verarbeitungszeit_ms INTEGER,
                    tokens_verwendet INTEGER,
                    vertrauen_score REAL,
                    verwendete_quellen TEXT,
                    feedback_bewertung INTEGER,
                    feedback_kommentar TEXT,
                    erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ip_adresse TEXT,
                    benutzer_agent TEXT
                )
            ''')
            
            # 6. System-Performance-Metriken
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS performance_metriken (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metrik_typ TEXT,
                    metrik_name TEXT,
                    wert REAL,
                    einheit TEXT,
                    gemessen_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    zusatz_info TEXT
                )
            ''')
            
            # 7. Volltext-Suche-Tabelle
            cursor.execute('''
                CREATE VIRTUAL TABLE IF NOT EXISTS volltext_suche USING fts5(
                    content,
                    datei_name,
                    typ,
                    kategorien,
                    schlagwoerter,
                    content_id UNINDEXED
                )
            ''')
            
            self.create_indexes(cursor)
            conn.commit()
    
    def create_indexes(self, cursor):
        """Erstellt Performance-Indizes"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_auftraege_status ON auftraege_enhanced(status)",
            "CREATE INDEX IF NOT EXISTS idx_auftraege_region ON auftraege_enhanced(region)",
            "CREATE INDEX IF NOT EXISTS idx_auftraege_erstellt ON auftraege_enhanced(erstellt_am)",
            "CREATE INDEX IF NOT EXISTS idx_auftraege_prioritaet ON auftraege_enhanced(prioritaet)",
            
            "CREATE INDEX IF NOT EXISTS idx_datei_typ ON datei_metadaten(typ)",
            "CREATE INDEX IF NOT EXISTS idx_datei_hash ON datei_metadaten(hash_md5)",
            "CREATE INDEX IF NOT EXISTS idx_datei_verarbeitet ON datei_metadaten(verarbeitet_am)",
            "CREATE INDEX IF NOT EXISTS idx_datei_ocr_status ON datei_metadaten(ocr_status)",
            
            "CREATE INDEX IF NOT EXISTS idx_ocr_datei ON ocr_ergebnisse(datei_id)",
            "CREATE INDEX IF NOT EXISTS idx_ocr_vertrauen ON ocr_ergebnisse(vertrauen_score)",
            
            "CREATE INDEX IF NOT EXISTS idx_abk_kategorie ON abkuerzungen_enhanced(kategorie)",
            "CREATE INDEX IF NOT EXISTS idx_abk_haeufigkeit ON abkuerzungen_enhanced(verwendung_haeufigkeit)",
            
            "CREATE INDEX IF NOT EXISTS idx_ki_sitzung ON ki_interaktionen(sitzung_id)",
            "CREATE INDEX IF NOT EXISTS idx_ki_erstellt ON ki_interaktionen(erstellt_am)",
            "CREATE INDEX IF NOT EXISTS idx_ki_performance ON ki_interaktionen(verarbeitungszeit_ms)",
            
            "CREATE INDEX IF NOT EXISTS idx_performance_typ ON performance_metriken(metrik_typ)",
            "CREATE INDEX IF NOT EXISTS idx_performance_zeit ON performance_metriken(gemessen_am)"
        ]
        
        for index in indexes:
            try:
                cursor.execute(index)
            except sqlite3.Error as e:
                self.logger.warning(f"Index creation failed: {e}")
    
    def init_analytics_schema(self):
        """Erstellt Analytics-Datenbank für Berichte"""
        with sqlite3.connect(self.analytics_db) as conn:
            cursor = conn.cursor()
            
            # Tägliche Statistiken
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_stats (
                    datum DATE PRIMARY KEY,
                    neue_auftraege INTEGER DEFAULT 0,
                    erledigte_auftraege INTEGER DEFAULT 0,
                    durchschnittliche_bearbeitungszeit REAL,
                    ki_anfragen INTEGER DEFAULT 0,
                    neue_dateien INTEGER DEFAULT 0,
                    ocr_verarbeitungen INTEGER DEFAULT 0,
                    durchschnittliche_ocr_qualitaet REAL,
                    system_uptime_stunden REAL,
                    fehler_anzahl INTEGER DEFAULT 0
                )
            ''')
            
            # Wöchentliche Trends
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS weekly_trends (
                    woche_jahr TEXT PRIMARY KEY,
                    auftraege_trend REAL,
                    performance_trend REAL,
                    qualitaets_trend REAL,
                    benutzer_zufriedenheit REAL
                )
            ''')
            
            # Top-Queries und häufige Probleme
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS query_analytics (
                    query_hash TEXT PRIMARY KEY,
                    query_text TEXT,
                    haeufigkeit INTEGER DEFAULT 1,
                    durchschnittliche_antwortzeit REAL,
                    erfolgsrate REAL,
                    letzte_verwendung TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
    
    def migrate_legacy_data(self):
        """Migriert Daten aus altem Schema"""
        legacy_tables = ['auftraege', 'datei_daten', 'abkuerzungen', 'training_log']
        
        with sqlite3.connect(self.main_db) as conn:
            cursor = conn.cursor()
            
            for table in legacy_tables:
                try:
                    # Prüfe ob alte Tabelle existiert
                    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
                    if cursor.fetchone():
                        self.logger.info(f"Migriere Daten aus {table}")
                        self._migrate_table_data(cursor, table)
                except sqlite3.Error as e:
                    self.logger.error(f"Migration von {table} fehlgeschlagen: {e}")
    
    def _migrate_table_data(self, cursor, table_name: str):
        """Migriert spezifische Tabellendaten"""
        if table_name == 'auftraege':
            cursor.execute('''
                INSERT OR IGNORE INTO auftraege_enhanced 
                (auftragsnummer, region, beschreibung, fehlercode, festnetznummer, status, server_anmeldung)
                SELECT auftragsnummer, region, beschreibung, fehlercode, festnetznummer, status, server_anmeldung
                FROM auftraege
            ''')
        
        elif table_name == 'datei_daten':
            cursor.execute('''
                INSERT OR IGNORE INTO datei_metadaten 
                (datei_name, typ, volltext_inhalt, hash_md5)
                SELECT datei_name, typ, inhalt, hash
                FROM datei_daten
            ''')
        
        elif table_name == 'abkuerzungen':
            cursor.execute('''
                INSERT OR IGNORE INTO abkuerzungen_enhanced 
                (code, bedeutung, pdf_referenzen)
                SELECT code, bedeutung, pdf_referenz
                FROM abkuerzungen
            ''')
        
        elif table_name == 'training_log':
            cursor.execute('''
                INSERT OR IGNORE INTO ki_interaktionen 
                (frage, antwort, erstellt_am)
                SELECT question, answer, timestamp
                FROM training_log
                WHERE question IS NOT NULL
            ''')
    
    def create_backup(self, backup_type: str = "manual") -> str:
        """Erstellt vollständiges Backup mit Kompression"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"eren_backup_{backup_type}_{timestamp}"
        backup_path = self.backup_dir / backup_name
        
        backup_path.mkdir(exist_ok=True)
        
        try:
            # Datenbanken kopieren
            if self.main_db.exists():
                shutil.copy2(self.main_db, backup_path / "eren_assist.db")
            if self.analytics_db.exists():
                shutil.copy2(self.analytics_db, backup_path / "eren_analytics.db")
            
            # Metadaten erstellen
            metadata = {
                "backup_type": backup_type,
                "created_at": timestamp,
                "database_version": self.get_database_version(),
                "file_count": len(list((self.base_dir / "2_PDF_Archiv").glob("*.*"))),
                "backup_size_mb": self._calculate_folder_size(backup_path)
            }
            
            with open(backup_path / "backup_metadata.json", 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, default=str)
            
            self.logger.info(f"Backup erstellt: {backup_path}")
            return str(backup_path)
            
        except Exception as e:
            self.logger.error(f"Backup fehlgeschlagen: {e}")
            return ""
    
    def _calculate_folder_size(self, folder_path: Path) -> float:
        """Berechnet Ordnergröße in MB"""
        total_size = sum(f.stat().st_size for f in folder_path.rglob('*') if f.is_file())
        return round(total_size / (1024 * 1024), 2)
    
    def optimize_database(self):
        """Führt Datenbankoptimierungen durch"""
        with sqlite3.connect(self.main_db) as conn:
            cursor = conn.cursor()
            
            # VACUUM für Speicherplatz-Optimierung
            cursor.execute("VACUUM")
            
            # ANALYZE für Query-Planer-Optimierung  
            cursor.execute("ANALYZE")
            
            # Bereinige alte Performance-Daten (älter als 30 Tage)
            cutoff_date = datetime.now() - timedelta(days=30)
            cursor.execute(
                "DELETE FROM performance_metriken WHERE gemessen_am < ?",
                (cutoff_date,)
            )
            
            conn.commit()
        
        self.logger.info("Datenbankoptimierung abgeschlossen")
    
    def get_database_version(self) -> str:
        """Gibt aktuelle Datenbankversion zurück"""
        try:
            with sqlite3.connect(self.main_db) as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA user_version")
                version = cursor.fetchone()[0]
                return f"v{version}.0"
        except:
            return "v1.0"
    
    def update_fulltext_search(self):
        """Aktualisiert Volltext-Suchindex"""
        with sqlite3.connect(self.main_db) as conn:
            cursor = conn.cursor()
            
            # Lösche alten Index
            cursor.execute("DELETE FROM volltext_suche")
            
            # Lade alle verarbeiteten Dateien
            cursor.execute('''
                SELECT id, datei_name, typ, volltext_inhalt, kategorien, schlagwoerter
                FROM datei_metadaten
                WHERE volltext_inhalt IS NOT NULL AND volltext_inhalt != ''
            ''')
            
            files = cursor.fetchall()
            
            # Füge zu Volltext-Index hinzu
            for file_data in files:
                cursor.execute('''
                    INSERT INTO volltext_suche 
                    (content, datei_name, typ, kategorien, schlagwoerter, content_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', file_data[3:] + (file_data[0],))
            
            conn.commit()
        
        self.logger.info(f"Volltext-Index mit {len(files)} Dateien aktualisiert")
    
    def search_content(self, query: str, limit: int = 20) -> List[Dict]:
        """Erweiterte Volltext-Suche mit Ranking"""
        with sqlite3.connect(self.main_db) as conn:
            cursor = conn.cursor()
            
            # FTS5-Suche mit Ranking
            cursor.execute('''
                SELECT 
                    v.datei_name,
                    v.typ,
                    v.kategorien,
                    snippet(volltext_suche, 0, '<mark>', '</mark>', '...', 64) as snippet,
                    rank,
                    d.groesse_bytes,
                    d.erstellt_am
                FROM volltext_suche v
                JOIN datei_metadaten d ON v.content_id = d.id
                WHERE volltext_suche MATCH ?
                ORDER BY rank
                LIMIT ?
            ''', (query, limit))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'datei_name': row[0],
                    'typ': row[1],
                    'kategorien': row[2],
                    'snippet': row[3],
                    'relevanz': row[4],
                    'groesse': row[5],
                    'erstellt_am': row[6]
                })
            
            return results
    
    def record_performance_metric(self, metrik_typ: str, metrik_name: str, 
                                 wert: float, einheit: str = "", zusatz_info: str = ""):
        """Speichert Performance-Metrik"""
        with sqlite3.connect(self.main_db) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO performance_metriken 
                (metrik_typ, metrik_name, wert, einheit, zusatz_info)
                VALUES (?, ?, ?, ?, ?)
            ''', (metrik_typ, metrik_name, wert, einheit, zusatz_info))
            conn.commit()
    
    def get_performance_summary(self, days: int = 7) -> Dict:
        """Gibt Performance-Zusammenfassung zurück"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        with sqlite3.connect(self.main_db) as conn:
            cursor = conn.cursor()
            
            # Durchschnittliche Antwortzeiten
            cursor.execute('''
                SELECT AVG(verarbeitungszeit_ms) as avg_response_time
                FROM ki_interaktionen 
                WHERE erstellt_am > ?
            ''', (cutoff_date,))
            avg_response = cursor.fetchone()[0] or 0
            
            # Anzahl Interaktionen
            cursor.execute('''
                SELECT COUNT(*) as total_queries
                FROM ki_interaktionen 
                WHERE erstellt_am > ?
            ''', (cutoff_date,))
            total_queries = cursor.fetchone()[0]
            
            # OCR-Performance
            cursor.execute('''
                SELECT AVG(vertrauen_score) as avg_ocr_confidence
                FROM ocr_ergebnisse 
                WHERE verarbeitet_am > ?
            ''', (cutoff_date,))
            avg_ocr = cursor.fetchone()[0] or 0
            
            return {
                'durchschnittliche_antwortzeit_ms': round(avg_response, 2),
                'gesamt_anfragen': total_queries,
                'durchschnittliche_ocr_qualitaet': round(avg_ocr, 2),
                'zeitraum_tage': days
            }

# Utility-Funktionen für einfache Verwendung
def setup_enhanced_database():
    """Einfache Setup-Funktion"""
    print("🚀 Initialisiere Enhanced Database...")
    db = EnhancedDatabaseEngine()
    
    print("📊 Migriere bestehende Daten...")
    db.migrate_legacy_data()
    
    print("🔍 Erstelle Volltext-Suchindex...")
    db.update_fulltext_search()
    
    print("💾 Erstelle Backup...")
    backup_path = db.create_backup("initial_upgrade")
    
    print("⚡ Optimiere Datenbank...")
    db.optimize_database()
    
    print("✅ Enhanced Database Setup abgeschlossen!")
    print(f"📁 Backup erstellt: {backup_path}")
    
    return db

if __name__ == "__main__":
    # Automatisches Setup beim direkten Ausführen
    enhanced_db = setup_enhanced_database()
    
    # Performance-Test
    print("\n🧪 Performance-Test...")
    start_time = time.time()
    results = enhanced_db.search_content("JustGo Verfahren", limit=10)
    search_time = (time.time() - start_time) * 1000
    
    print(f"Suche dauerte: {search_time:.2f}ms")
    print(f"Gefundene Ergebnisse: {len(results)}")
    
    # Performance-Metrik speichern
    enhanced_db.record_performance_metric(
        "search", "fulltext_search", search_time, "ms", "Test-Suche nach 'JustGo Verfahren'"
    )
    
    # Performance-Zusammenfassung
    summary = enhanced_db.get_performance_summary()
    print("\n📈 Performance-Zusammenfassung (letzte 7 Tage):")
    for key, value in summary.items():
        print(f"  {key}: {value}")
