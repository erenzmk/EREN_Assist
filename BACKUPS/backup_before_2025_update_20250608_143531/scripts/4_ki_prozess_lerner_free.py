import os
# Unterdrückt CUDA-Fehlermeldungen
import ctypes
try:
    ctypes.CDLL("libcuda.so").cuInit(0)
except:
    pass

os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
import os
# Unterdrückt CUDA-Fehlermeldungen
import ctypes
try:
    ctypes.CDLL("libcuda.so").cuInit(0)
except:
    pass

os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
import os
# Unterdrückt CUDA-Fehlermeldungen
import ctypes
try:
    ctypes.CDLL("libcuda.so").cuInit(0)
except:
    pass

os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
import os
# Unterdrückt CUDA-Fehlermeldungen
import ctypes
try:
    ctypes.CDLL("libcuda.so").cuInit(0)
except:
    pass

os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
import os
# Unterdrückt CUDA-Fehlermeldungen
import ctypes
try:
    ctypes.CDLL("libcuda.so").cuInit(0)
except:
    pass

os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
import os
# Unterdrückt CUDA-Fehlermeldungen
import ctypes
try:
    ctypes.CDLL("libcuda.so").cuInit(0)
except:
    pass

os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
import os
# Unterdrückt CUDA-Fehlermeldungen
import ctypes
try:
    ctypes.CDLL("libcuda.so").cuInit(0)
except:
    pass

os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
import os
# Unterdrückt CUDA-Fehlermeldungen
import ctypes
try:
    ctypes.CDLL("libcuda.so").cuInit(0)
except:
    pass

os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
import os
# Unterdrückt CUDA-Fehlermeldungen
import ctypes
try:
    ctypes.CDLL("libcuda.so").cuInit(0)
except:
    pass

os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
import os
# Unterdrückt CUDA-Fehlermeldungen
import ctypes
try:
    ctypes.CDLL("libcuda.so").cuInit(0)
except:
    pass

os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
import os
# Unterdrückt CUDA-Fehlermeldungen
import ctypes
try:
    ctypes.CDLL("libcuda.so").cuInit(0)
except:
    pass

os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
import os
# Unterdrückt CUDA-Fehlermeldungen
import ctypes
try:
    ctypes.CDLL("libcuda.so").cuInit(0)
except:
    pass

os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
import os
# Unterdrückt CUDA-Fehlermeldungen
import ctypes
try:
    ctypes.CDLL("libcuda.so").cuInit(0)
except:
    pass

os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
import os
# Unterdrückt CUDA-Fehlermeldungen
import ctypes
try:
    ctypes.CDLL("libcuda.so").cuInit(0)
except:
    pass

os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
import os
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
import sqlite3
import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS  # Korrigierter Import
from langchain_community.embeddings import GPT4AllEmbeddings  # Korrigierter Import
from langchain.chains import RetrievalQA
from langchain_community.llms import GPT4All  # Korrigierter Import
from langchain.prompts import PromptTemplate

# Konfiguration
BASE_DIR = r"C:\EREN_Assist"
DB_PATH = os.path.join(BASE_DIR, "1_Datenbank", "eren_assist.db")
MODEL_DIR = os.path.join(BASE_DIR, "ki_modelle")
MODEL_FILE = "mistral-7b-openorca.Q5_K_M.gguf"
os.makedirs(MODEL_DIR, exist_ok=True)

def lade_dokumente():
    """Lädt alle Dokumente aus der Datenbank"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT inhalt FROM datei_daten")
    dokumente = [row[0] for row in c.fetchall()]
    conn.close()
    print(f"Geladene Dokumente: {len(dokumente)}")
    return dokumente

def trainiere_ki():
    """Trainiert das KI-Modell mit den Dokumenten"""
    # 1. Dokumente laden
    dokumente = lade_dokumente()
    if not dokumente:
        print("Keine Dokumente gefunden! Bitte zuerst Dateien verarbeiten.")
        return None
    
    # 2. Text in Chunks aufteilen
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    texts = text_splitter.create_documents(dokumente)
    print(f"Erstellte Text-Chunks: {len(texts)}")
    
    # 3. Embeddings generieren (lokal!)
    embeddings = GPT4AllEmbeddings()
    
    # 4. Vector Store erstellen
    vectorstore = FAISS.from_documents(texts, embeddings)
    vectorstore.save_local(os.path.join(MODEL_DIR, "prozess_db_free"))
    print("Vektordatenbank erfolgreich gespeichert")
    
    # 5. Prompt-Template für bessere Antworten
    template = """Verwende die folgenden Informationen, um die Frage zu beantworten.
    Wenn du die Antwort nicht weißt, sage, dass du es nicht weißt, erfinde keine Antwort.
    Kontext: {context}
    Frage: {question}
    Hilfreiche Antwort:"""
    
    QA_PROMPT = PromptTemplate(
        template=template,
        input_variables=["context", "question"]
    )
    
    # 6. QA-Kette erstellen mit lokalem Modell
    llm = GPT4All(
        model=os.path.join(MODEL_DIR, MODEL_FILE),
        max_tokens=2048,
        # temperature-Parameter entfernt0.7,  # Korrigierter Parametername (vorher 'temp')
        verbose=False
    )
    
    qa = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever(),
        return_source_documents=True,
        chain_type_kwargs={"prompt": QA_PROMPT}
    )
    
    return qa

def interaktive_sitzung(qa_system):
    """Startet eine interaktive Frage-Antwort-Sitzung"""
    print("\nKI-Prozessassistent ist bereit. Geben Sie 'exit' ein, um zu beenden.")
    while True:
        frage = input("\nIhre Frage: ")
        if frage.lower() in ['exit', 'beenden', 'quit']:
            break
        try:
            result = qa_system({"query": frage})
            antwort = result['result']
            print(f"\nAntwort: {antwort}")
            
            # Zeige Quellen für Transparenz
            print("\nQuellen:")
            for i, doc in enumerate(result['source_documents'][:2]):
                print(f"{i+1}. {doc.page_content[:150]}...")
        except Exception as e:
            print(f"Fehler: {str(e)}")

if __name__ == "__main__":
    print("Starte Training des lokalen KI-Modells (kann einige Minuten dauern)...")
    qa_system = trainiere_ki()
    
    if qa_system:
        beispiele = [
            "Welche Schritte sind bei einem JustGo-Eintrag erforderlich?",
            "Wie gehe ich mit Fehlercode 0xFA3B um?",
            "Was ist das Protokoll für nicht erreichbare Kunden?"
        ]
        
        print("\nBeispielantworten:")
        for frage in beispiele:
            print(f"\nFrage: {frage}")
            result = qa_system({"query": frage})
            antwort = result['result']
            print(f"Antwort: {antwort[:300]}{'...' if len(antwort) > 300 else ''}")
        
        # Interaktive Sitzung starten
        interaktive_sitzung(qa_system)