#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EREN-kompatibles PDF Update Skript
Funktioniert mit der bestehenden EREN Assist Datenbankstruktur
"""

import os
import sqlite3
import hashlib
import time
import io
from pathlib import Path
from datetime import datetime
from typing import List, Dict

# OCR und PDF Bibliotheken (falls verfügbar)
try:
    import fitz  # PyMuPDF
    import pytesseract
    from PIL import Image
    PDF_PROCESSING_AVAILABLE = True
except ImportError:
    PDF_PROCESSING_AVAILABLE = False
    print("⚠️ OCR-Bibliotheken nicht verfügbar. Nur Metadaten werden verarbeitet.")

class ErenCompatibleUpdater:
    """Kompatibles Update-Tool für bestehende EREN Assist Datenbank"""
    
    def __init__(self):
        self.base_dir = Path("C:/EREN_Assist")
        self.pdf_dir = self.base_dir / "2_PDF_Archiv"
        self.db_path = self.base_dir / "1_Datenbank" / "eren_assist.db"
        
        # Analysiere bestehende Datenbankstruktur
        self.db_structure = self.analyze_database_structure()
        print(f"✅ Verwende Tabellenstruktur: {list(self.db_structure.keys())}")
    
    def analyze_database_structure(self) -> Dict[str, List[str]]:
        """Analysiert die bestehende Datenbankstruktur"""
        structure = {}
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Alle Tabellen finden
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                for table in tables:
                    # Spalten für jede Tabelle
                    cursor.execute(f"PRAGMA table_info({table})")
                    columns = [col[1] for col in cursor.fetchall()]
                    structure[table] = columns
                    
                return structure
                
        except Exception as e:
            print(f"❌ Datenbankanalyse fehlgeschlagen: {e}")
            # Fallback zur Standard-EREN-Struktur
            return {
                'datei_daten': ['datei_name', 'typ', 'inhalt', 'hash']
            }
    
    def get_primary_table(self) -> str:
        """Findet die Haupttabelle für Dateien"""
        candidates = ['datei_daten', 'datei_metadaten', 'pdf_daten']
        
        for candidate in candidates:
            if candidate in self.db_structure:
                return candidate
        
        # Fallback
        return list(self.db_structure.keys())[0] if self.db_structure else 'datei_daten'
    
    def calculate_file_hash(self, file_path: Path) -> str:
        """Berechnet MD5-Hash einer Datei"""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            print(f"❌ Hash-Berechnung fehlgeschlagen für {file_path}: {e}")
            return ""
    
    def extract_text_from_pdf(self, file_path: Path) -> str:
        """Extrahiert Text aus PDF (mit OCR falls nötig)"""
        if not PDF_PROCESSING_AVAILABLE:
            return f"[PDF-Text aus {file_path.name} - OCR-Bibliotheken nicht verfügbar]"
        
        try:
            text_content = []
            
            with fitz.open(file_path) as pdf_doc:
                for page_num in range(len(pdf_doc)):
                    page = pdf_doc.load_page(page_num)
                    
                    # Versuche zuerst Text zu extrahieren
                    text = page.get_text()
                    
                    if text.strip():
                        text_content.append(text)
                    else:
                        # Falls kein Text, versuche OCR (mit korrigiertem io import)
                        try:
                            pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
                            img_data = pix.pil_tobytes(format="PNG")
                            img = Image.open(io.BytesIO(img_data))  # io korrekt importiert
                            ocr_text = pytesseract.image_to_string(img, lang='deu+eng')
                            text_content.append(ocr_text)
                        except Exception as ocr_error:
                            print(f"⚠️ OCR fehlgeschlagen für Seite {page_num}: {ocr_error}")
                            text_content.append(f"[OCR-Fehler auf Seite {page_num}]")
            
            return "\n\n".join(text_content)
            
        except Exception as e:
            print(f"❌ PDF-Textextraktion fehlgeschlagen für {file_path}: {e}")
            return f"[Fehler bei Textextraktion aus {file_path.name}: {str(e)}]"
    
    def is_file_in_database(self, file_path: Path) -> bool:
        """Prüft ob Datei bereits in Datenbank existiert (kompatibel)"""
        try:
            table = self.get_primary_table()
            columns = self.db_structure[table]
            
            # Verschiedene Spaltennamen für Dateiname probieren
            name_column = None
            for col in ['datei_name', 'name', 'filename', 'file_name']:
                if col in columns:
                    name_column = col
                    break
            
            if not name_column:
                print("⚠️ Keine Dateiname-Spalte gefunden")
                return False
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    f"SELECT COUNT(*) FROM {table} WHERE {name_column} = ?",
                    (file_path.name,)
                )
                return cursor.fetchone()[0] > 0
                
        except Exception as e:
            print(f"❌ Datenbankprüfung fehlgeschlagen: {e}")
            return False
    
    def add_pdf_to_database(self, file_path: Path) -> bool:
        """Fügt PDF zur Datenbank hinzu (kompatibel mit bestehender Struktur)"""
        try:
            print(f"🔄 Verarbeite: {file_path.name}")
            
            table = self.get_primary_table()
            columns = self.db_structure[table]
            
            # Text extrahieren
            print(f"   📄 Extrahiere Text...")
            content = self.extract_text_from_pdf(file_path)
            
            # Hash berechnen
            file_hash = self.calculate_file_hash(file_path)
            
            # Datenbank aktualisieren (nur mit verfügbaren Spalten)
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Dynamische Insert-Query basierend auf verfügbaren Spalten
                insert_data = {}
                
                # Standard-Zuordnungen
                if 'datei_name' in columns:
                    insert_data['datei_name'] = file_path.name
                elif 'name' in columns:
                    insert_data['name'] = file_path.name
                
                if 'typ' in columns:
                    insert_data['typ'] = 'pdf'
                elif 'file_type' in columns:
                    insert_data['file_type'] = 'pdf'
                
                if 'inhalt' in columns:
                    insert_data['inhalt'] = content
                elif 'content' in columns:
                    insert_data['content'] = content
                elif 'text' in columns:
                    insert_data['text'] = content
                
                if 'hash' in columns:
                    insert_data['hash'] = file_hash
                elif 'hash_md5' in columns:
                    insert_data['hash_md5'] = file_hash
                
                if insert_data:
                    # Insert oder Update
                    if self.is_file_in_database(file_path):
                        # Update (vereinfacht)
                        set_clause = ", ".join([f"{k} = ?" for k in insert_data.keys() if k not in ['datei_name', 'name']])
                        name_col = 'datei_name' if 'datei_name' in columns else 'name'
                        
                        if set_clause:
                            update_values = [v for k, v in insert_data.items() if k not in ['datei_name', 'name']]
                            update_values.append(file_path.name)
                            
                            cursor.execute(
                                f"UPDATE {table} SET {set_clause} WHERE {name_col} = ?",
                                update_values
                            )
                            print(f"   ✅ Aktualisiert in Datenbank")
                    else:
                        # Insert
                        placeholders = ", ".join(["?" for _ in insert_data])
                        column_names = ", ".join(insert_data.keys())
                        
                        cursor.execute(
                            f"INSERT INTO {table} ({column_names}) VALUES ({placeholders})",
                            list(insert_data.values())
                        )
                        print(f"   ✅ Hinzugefügt zur Datenbank")
                    
                    conn.commit()
                    return True
                else:
                    print(f"   ⚠️ Keine kompatiblen Spalten gefunden")
                    return False
                
        except Exception as e:
            print(f"❌ Fehler beim Hinzufügen von {file_path.name}: {e}")
            return False
    
    def scan_and_update(self) -> Dict[str, int]:
        """Scannt PDF-Archiv und aktualisiert Datenbank"""
        stats = {
            "found": 0,
            "new": 0,
            "updated": 0,
            "errors": 0,
            "skipped": 0
        }
        
        print("🔍 Scanne PDF-Archiv...")
        print(f"📁 Verzeichnis: {self.pdf_dir}")
        print(f"🗄️ Datenbank-Tabelle: {self.get_primary_table()}")
        
        try:
            # Alle PDF-Dateien finden
            pdf_files = list(self.pdf_dir.glob("*.pdf"))
            stats["found"] = len(pdf_files)
            
            if not pdf_files:
                print("⚠️ Keine PDF-Dateien gefunden!")
                return stats
            
            print(f"📊 {len(pdf_files)} PDF-Dateien gefunden")
            print("=" * 50)
            
            for i, pdf_file in enumerate(pdf_files, 1):
                print(f"[{i}/{len(pdf_files)}] {pdf_file.name}")
                
                try:
                    # Prüfe ob bereits in Datenbank
                    if self.is_file_in_database(pdf_file):
                        print(f"   ⏭️ Bereits in Datenbank - übersprungen")
                        stats["skipped"] += 1
                    else:
                        # Neue Datei
                        if self.add_pdf_to_database(pdf_file):
                            stats["new"] += 1
                        else:
                            stats["errors"] += 1
                            
                except Exception as e:
                    print(f"   ❌ Fehler: {e}")
                    stats["errors"] += 1
                
                # Kurze Pause
                time.sleep(0.1)
            
            print("=" * 50)
            print("📊 ZUSAMMENFASSUNG:")
            print(f"   📄 Gefunden: {stats['found']}")
            print(f"   ✅ Neu hinzugefügt: {stats['new']}")
            print(f"   🔄 Aktualisiert: {stats['updated']}")
            print(f"   ⏭️ Übersprungen: {stats['skipped']}")
            print(f"   ❌ Fehler: {stats['errors']}")
            print("=" * 50)
            
            return stats
            
        except Exception as e:
            print(f"❌ Scan-Fehler: {e}")
            return stats
    
    def show_database_info(self):
        """Zeigt Informationen über die Datenbank"""
        print("🗄️ DATENBANKSTRUKTUR:")
        print("=" * 40)
        
        for table, columns in self.db_structure.items():
            print(f"📋 Tabelle: {table}")
            print(f"   Spalten: {', '.join(columns)}")
            
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    print(f"   Datensätze: {count}")
            except:
                print(f"   Datensätze: [Fehler beim Zählen]")
            print()


def main():
    """Hauptfunktion"""
    print("=" * 60)
    print("    EREN-KOMPATIBLES PDF UPDATE TOOL")
    print("=" * 60)
    print()
    
    updater = ErenCompatibleUpdater()
    
    try:
        while True:
            print("\n📋 Verfügbare Aktionen:")
            print("1. PDF-Archiv scannen und Datenbank aktualisieren")
            print("2. Datenbankstruktur anzeigen")
            print("3. Beenden")
            
            choice = input("\nAktion wählen (1-3): ").strip()
            
            if choice == "1":
                print("\n🚀 Starte PDF-Scan und Datenbank-Update...")
                stats = updater.scan_and_update()
                
                if stats["new"] > 0:
                    print(f"\n✅ {stats['new']} neue PDFs zur Datenbank hinzugefügt!")
                    print("💡 Sie können jetzt EREN Assist starten und die neuen PDFs abfragen.")
                elif stats["skipped"] > 0:
                    print(f"\n ℹ️ Alle {stats['skipped']} PDFs sind bereits in der Datenbank.")
                
            elif choice == "2":
                updater.show_database_info()
                
            elif choice == "3":
                print("\n👋 Auf Wiedersehen!")
                break
                
            else:
                print("❌ Ungültige Auswahl! Bitte 1-3 eingeben.")
    
    except KeyboardInterrupt:
        print("\n\n⏹️ Abgebrochen durch Benutzer")
    except Exception as e:
        print(f"\n❌ Unerwarteter Fehler: {e}")


if __name__ == "__main__":
    main()
