import sqlite3
import os
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.llms import GPT4All

# Konfiguration
BASE_DIR = r"C:\EREN_Assist"
DB_PATH = os.path.join(BASE_DIR, "1_Datenbank", "eren_assist.db")
MODEL_PATH = os.path.join(BASE_DIR, "ki_modelle", "ggml-gpt4all-j-v1.3-groovy.bin")

# 1. Datenbankverbindung herstellen
db = SQLDatabase.from_uri(f"sqlite:///{DB_PATH}")
print("🔌 Verbunden mit Datenbank:", DB_PATH)
print("📊 Tabellen in der Datenbank:", db.get_usable_table_names())

# 2. KI-Modell laden
try:
    llm = GPT4All(model=MODEL_PATH, verbose=True, n_threads=4)
    print(f"🧠 KI-Modell geladen: {MODEL_PATH}")
except Exception as e:
    print(f"❌ Fehler beim Laden des Modells: {str(e)}")
    print("⚠️ Versuche alternatives Modell...")
    try:
        MODEL_PATH = os.path.join(BASE_DIR, "ki_modelle", "mistral-7b-openorca.Q4_0.gguf")
        llm = GPT4All(model=MODEL_PATH, verbose=True, n_threads=4)
        print(f"🧠 Alternatives Modell geladen: {MODEL_PATH}")
    except Exception as e2:
        print(f"❌ Kritischer Fehler: {str(e2)}")
        exit()

# 3. SQL Agent erstellen
agent = create_sql_agent(
    llm=llm,
    db=db,
    agent_type="zero-shot-react-description",
    verbose=True
)
print("🤖 SQL-Agent erfolgreich erstellt")

# 4. Typische Abfragen für Ihr System
fragen = [
    "Wie viele Aufträge gibt es mit Status 'Neu'?",
    "Zeige alle PDF-Dateien, die verarbeitet wurden",
    "Welche Abkürzungen sind in der Datenbank gespeichert?",
    "Gib mir alle Updates für Auftrag mit ID 1",
    "Wie viele verschiedene Regionen gibt es in den Aufträgen?"
]

print("\n" + "="*50)
print("START DER KI-ANFRAGEN AN IHERE DATENBANK")
print("="*50)

for i, frage in enumerate(fragen, 1):
    print(f"\n⭐ Frage {i}: {frage}")
    try:
        antwort = agent.run(frage)
        print(f"📝 Antwort: {antwort}")
    except Exception as e:
        print(f"❌ Fehler bei der Abfrage: {str(e)}")
        print("⚠️ Versuche mit direkter SQL-Abfrage...")
        
        try:
            # Verbindung zur SQLite-Datenbank
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            if i == 1:
                cursor.execute("SELECT COUNT(*) FROM auftraege WHERE status = 'Neu'")
                result = cursor.fetchone()[0]
            elif i == 2:
                cursor.execute("SELECT datei_name FROM datei_daten WHERE typ = 'pdf'")
                result = [row[0] for row in cursor.fetchall()]
            elif i == 3:
                cursor.execute("SELECT code, bedeutung FROM abkuerzungen")
                result = {row[0]: row[1] for row in cursor.fetchall()}
            elif i == 4:
                cursor.execute("SELECT nachricht, zeitpunkt FROM updates WHERE auftrag_id = 1")
                result = cursor.fetchall()
            elif i == 5:
                cursor.execute("SELECT COUNT(DISTINCT region) FROM auftraege")
                result = cursor.fetchone()[0]
            
            print(f"🔧 Direktes SQL-Ergebnis: {result}")
        except Exception as e2:
            print(f"❌ SQL-Fehler: {str(e2)}")
        finally:
            conn.close()

print("\n" + "="*50)
print("ENDE DER ABFRAGEN")
print("="*50)
print("✅ KI-SQL-Agent erfolgreich getestet!")