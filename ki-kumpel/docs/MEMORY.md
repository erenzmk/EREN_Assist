# Gedächtnis- und Wissenssystem

## Speicheraufbau
- **SQLite-Datei:** `data/memory.sqlite`
- **Tabellen:**
  - `interactions`: speichert alle Benutzer- und KI-Nachrichten (ts, role, content, meta)
  - `facts`: enthält zeitlose Fakten (ts, source, fact, importance)

## Workflow
1. Beim Start der Anwendung lädt `core.router.AssistantRouter` die letzten 30 Interaktionen.
2. Benutzerfragen und KI-Antworten werden unmittelbar mit `memory.memory_db.MemoryDB.add_interaction` persistiert.
3. `memory.knowledge_builder.KnowledgeBuilder.refresh_facts` analysiert regelmäßig die Interaktionen, extrahiert allgemeingültige Aussagen und speichert sie als Fakten.
4. `KnowledgeBuilder.get_relevant_facts(query)` liefert eine Liste passender Fakten, die als zusätzlicher Kontext an das LLM übergeben werden.

## Nutzung im Code
```python
from memory.memory_db import MemoryDB
from memory.knowledge_builder import KnowledgeBuilder

memory = MemoryDB()
knowledge = KnowledgeBuilder(memory)
last_entries = memory.get_recent_interactions(limit=30)
facts = knowledge.get_relevant_facts("Wie gehe ich mit CAD-Cases um?")
```

## Stilprofil
`memory.style_profile.apply_style` transformiert LLM-Antworten in den Eren-Stil. Dazu werden Beispieltexte aus `data/style_samples/*.txt` analysiert, um typische Anrede, Grußformel und Ton zu bestimmen.

## Erweiterungsideen
- Ersatz/Ergänzung von SQLite durch eine Vektor-Datenbank (FAISS, ChromaDB) für semantische Suche.
- Hintergrundprozess, der `KnowledgeBuilder.refresh_facts` periodisch über einen Scheduler aufruft.
- Export-Skripte für Backups der SQLite-Datei und Logfiles.
