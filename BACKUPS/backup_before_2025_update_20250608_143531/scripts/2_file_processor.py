import sqlite3
import os
import pytesseract
from PIL import Image
import pdfplumber
import docx
from pathlib import Path
import hashlib
import win32com.client

# Konfiguration
BASE_DIR = r"C:\EREN_Assist"
DB_PATH = os.path.join(BASE_DIR, "1_Datenbank", "eren_assist.db")
FILES_DIR = os.path.join(BASE_DIR, "2_PDF_Archiv")

# Tesseract OCR Pfad setzen
try:
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    # Test ob Tesseract verfügbar ist
    pytesseract.get_tesseract_version()
    print("Tesseract OCR erfolgreich gefunden!")
except (pytesseract.TesseractNotFoundError, FileNotFoundError):
    print("FEHLER: Tesseract OCR nicht gefunden. Bitte installieren Sie Tesseract von:")
    print("https://github.com/UB-Mannheim/tesseract/wiki")
    print("Setze Tesseract-Pfad auf Standardinstallation...")
    # Alternative Pfade versuchen
    possible_paths = [
        r'C:\Program Files\Tesseract-OCR\tesseract.exe',
        r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
        r'C:\Users\egencer\AppData\Local\Tesseract-OCR\tesseract.exe'
    ]
    for path in possible_paths:
        if os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
            print(f"Tesseract gefunden unter: {path}")
            break
    else:
        print("Tesseract nicht gefunden! Bildverarbeitung wird nicht funktionieren.")
        exit(1)

# Unterstützte Dateitypen
SUPPORTED_EXTS = {
    '.pdf': 'pdf',
    '.docx': 'word',
    '.doc': 'word',
    '.jpg': 'image',
    '.jpeg': 'image',
    '.png': 'image',
    '.txt': 'text'
}

def extrahiere_text(dateipfad):
    """Extrahiert Text aus verschiedenen Dateitypen"""
    ext = os.path.splitext(dateipfad)[1].lower()
    dateiname = os.path.basename(dateipfad)
    
    try:
        if ext in ['.pdf']:
            with pdfplumber.open(dateipfad) as pdf:
                return "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
        
        elif ext in ['.docx']:
            doc = docx.Document(dateipfad)
            return "\n".join([para.text for para in doc.paragraphs])
        
        elif ext in ['.doc']:
            # Verarbeitung alter Word-Dateien mit win32com
            word = win32com.client.Dispatch("Word.Application")
            word.visible = False
            doc = word.Documents.Open(dateipfad)
            text = doc.Content.Text
            doc.Close()
            word.Quit()
            return text
        
        elif ext in ['.jpg', '.jpeg', '.png']:
            img = Image.open(dateipfad)
            return pytesseract.image_to_string(img)
        
        elif ext == '.txt':
            with open(dateipfad, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
                
        else:
            return f"[Unterstützter Dateityp aber nicht implementiert: {ext}]"
                
    except Exception as e:
        return f"[FEHLER bei Verarbeitung: {str(e)}]"

def verarbeite_dateien():
    datei_daten = []
    for datei in os.listdir(FILES_DIR):
        dateipfad = os.path.join(FILES_DIR, datei)
        ext = os.path.splitext(datei)[1].lower()
        
        if ext in SUPPORTED_EXTS:
            try:
                text = extrahiere_text(dateipfad)
                # Datei-Hash für Änderungserkennung
                with open(dateipfad, 'rb') as f:
                    datei_hash = hashlib.md5(f.read()).hexdigest()
                
                datei_daten.append((datei, SUPPORTED_EXTS[ext], text, datei_hash))
                print(f"✓ {datei} verarbeitet ({SUPPORTED_EXTS[ext]})")
            except Exception as e:
                print(f"✗ Fehler bei {datei}: {str(e)}")
    
    return datei_daten

def speichere_in_db(datei_daten):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS datei_daten (
                    datei_name TEXT PRIMARY KEY,
                    typ TEXT,
                    inhalt TEXT,
                    hash TEXT
                )''')
                
    for name, typ, inhalt, hash_val in datei_daten:
        c.execute('''INSERT OR REPLACE INTO datei_daten 
                     VALUES (?, ?, ?, ?)''', (name, typ, inhalt, hash_val))
    
    conn.commit()
    conn.close()
    print(f"\n{len(datei_daten)} Dateien in Datenbank gespeichert")

if __name__ == "__main__":
    # Ordnerstruktur sicherstellen
    Path(FILES_DIR).mkdir(parents=True, exist_ok=True)
    
    datei_daten = verarbeite_dateien()
    if datei_daten:
        speichere_in_db(datei_daten)
    else:
        print("Keine verarbeitbaren Dateien gefunden. Unterstützte Formate:")
        print(", ".join(SUPPORTED_EXTS.keys()))
        print(f"Bitte Dateien in {FILES_DIR} ablegen und Skript erneut starten")