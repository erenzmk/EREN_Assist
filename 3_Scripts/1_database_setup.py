import sqlite3
import os
from pathlib import Path

# Pfade definieren
BASE_DIR = r"C:\EREN_Assist"
DB_DIR = os.path.join(BASE_DIR, "1_Datenbank")
DB_PATH = os.path.join(DB_DIR, "eren_assist.db")
SCRIPTS_DIR = os.path.join(BASE_DIR, "3_Scripts")

# Ordner erstellen
Path(DB_DIR).mkdir(parents=True, exist_ok=True)

# Datenbankverbindung
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Aufträge-Tabelle
c.execute('''CREATE TABLE IF NOT EXISTS auftraege (
                id INTEGER PRIMARY KEY,
                auftragsnummer TEXT,
                region TEXT,
                beschreibung TEXT,
                fehlercode TEXT,
                festnetznummer TEXT,
                status TEXT DEFAULT 'Neu',
                server_anmeldung INTEGER DEFAULT 0
             )''')

# Abkürzungslexikon
c.execute('''CREATE TABLE IF NOT EXISTS abkuerzungen (
                code TEXT PRIMARY KEY,
                bedeutung TEXT,
                pdf_referenz TEXT
             )''')

# Techniker-Updates
c.execute('''CREATE TABLE IF NOT EXISTS updates (
                auftrag_id INTEGER,
                zeitpunkt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                nachricht TEXT,
                FOREIGN KEY (auftrag_id) REFERENCES auftraege(id)
             )''')

# PDF-Daten
c.execute('''CREATE TABLE IF NOT EXISTS pdf_daten (
                pdf_name TEXT PRIMARY KEY,
                inhalt TEXT
             )''')

print(f"Datenbank erfolgreich erstellt unter: {DB_PATH}")
conn.commit()
conn.close()