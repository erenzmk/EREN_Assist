# Fortschrittsprotokoll

- Struktur auf `core/`, `memory/`, `ui/`, `docs/`, `data/`, `tests/` reorganisiert.
- Persistentes SQLite-Gedächtnis mit Interaktions- und Fakten-Tabellen implementiert.
- Wissensextraktion (`KnowledgeBuilder`) und Stilprofil (`apply_style`) integriert.
- Neues Dark-Mode-Chatfenster mit Enter/Shift+Enter-Logik erstellt.
- Tray, CLI und Overlay auf neue Architektur umgestellt.
- Dokumentation (`ARCHITECTURE.md`, `MEMORY.md`) ergänzt.
- SQLite-Speicher thread-sicher gemacht und Einstiegsskripte passen den Modulpfad automatisch an.
- Gemeinsames Bootstrap-Modul ergänzt, das zuverlässig die Projektwurzel findet (auch für Windows/Exe) und Importfehler wie `No module named 'ui'` verhindert.
