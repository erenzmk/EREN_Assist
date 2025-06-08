import sqlite3
import re
import os

# Pfade definieren
BASE_DIR = r"C:\EREN_Assist"
DB_PATH = os.path.join(BASE_DIR, "1_Datenbank", "eren_assist.db")

def finde_abkuerzungen(text):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Finde alle Codes im Text (Buchstaben/Zahlenkombinationen)
    codes = re.findall(r'\b[A-Z0-9]{3,8}\b', text.upper())
    ergebnisse = []
    
    for code in set(codes):  # Duplikate entfernen
        c.execute("SELECT bedeutung, pdf_referenz FROM abkuerzungen WHERE code=?", (code,))
        result = c.fetchone()
        if result:
            ergebnisse.append({
                'code': code,
                'bedeutung': result[0],
                'referenz': result[1]
            })
    
    conn.close()
    return ergebnisse

def manuell_hinzufuegen():
    print("\n--- Abkürzung manuell hinzufügen ---")
    code = input("Abkürzung: ").strip().upper()
    bedeutung = input("Bedeutung: ").strip()
    referenz = input("PDF-Dateiname (z.B. Handbuch.pdf): ").strip()
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO abkuerzungen VALUES (?, ?, ?)", 
              (code, bedeutung, referenz))
    conn.commit()
    conn.close()
    print(f"✓ '{code}' hinzugefügt")

if __name__ == "__main__":
    while True:
        text = input("\nAuftragstext eingeben (oder 'm' für manuell, 'q' zum Beenden): ")
        if text.lower() == 'q':
            break
        if text.lower() == 'm':
            manuell_hinzufuegen()
            continue
            
        abkuerzungen = finde_abkuerzungen(text)
        
        if abkuerzungen:
            print("\nErkannte Abkürzungen:")
            for abk in abkuerzungen:
                print(f"- {abk['code']}: {abk['bedeutung']}")
                print(f"  Referenz: {abk['referenz']}")
        else:
            print("Keine bekannten Abkürzungen gefunden. Manuell hinzufügen? (m)")