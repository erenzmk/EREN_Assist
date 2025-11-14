# Architekturüberblick KI-Kumpel

## Zielbild
Das Projekt ist in modulare Bereiche gegliedert, damit UI, Kernlogik und Gedächtnis klar getrennt bleiben. Der Code ist als wiederverwendbares Paket aufgebaut und kann sowohl als Desktop-App, Tray oder CLI genutzt werden.

## Ordnerstruktur
```
core/             # Basiskomponenten (Konfiguration, LLM, Screenshots, Router, Logging, TTS)
memory/           # Persistentes Gedächtnis, Wissensaufbereitung, Stilprofil
ui/               # Desktop-Oberflächen, Chatfenster, Tray & Overlay
src/              # Kompatibilitäts-Skripte für bestehende Einstiegspunkte
data/             # Persistente Daten (SQLite, Stil-Beispiele)
docs/             # Dokumentation und Fortschrittslog
logs/             # Rotierendes Logfile der Anwendung
assets/           # Icons und statische Ressourcen
tests/            # Platzhalter für zukünftige Tests
```

## Module & Verantwortlichkeiten
- **core.config**: Pfade, Modelle, Standard-Prompts, Intervallwerte.
- **core.logger**: zentrales Logging mit Rotationshandler.
- **core.screen_capture**: Screenshot-Utility inklusive Bereinigung.
- **core.tts**: gekapselte Text-to-Speech Ausgaben.
- **core.llm_client**: Wrapper für sämtliche OpenAI-Anfragen (Text & Vision).
- **core.router**: Vermittelt zwischen UI, Gedächtnis, Wissensbasis und LLM.

- **memory.memory_db**: SQLite-Schema und CRUD-Operationen für Interaktionen & Fakten.
- **memory.knowledge_builder**: extrahiert zeitlose Fakten aus Gesprächen und liefert relevante Fakten zu neuen Fragen.
- **memory.style_profile**: liest Beispieltexte, erzeugt Stilregeln und transformiert Antworten in den „Eren-Stil“.

- **ui.chat_window**: Modernes Chatfenster mit Dark-Theme, Enter=Send, Shift+Enter=Zeilenumbruch.
- **ui.app**: Haupt-Tkinter-Anwendung mit Buttons, Auto-Screenshots und Gedächtnis-Integration.
- **ui.tray**: System-Tray-Integration auf Basis der neuen Kernlogik.
- **ui.overlay**: Leichtgewichtige Overlay-Anzeige.

- **src/**: Stellt die bisherigen Einstiegspunkte (`ki_kumpel_app.py`, `assistant_core.py`, `assistant_tray.py`, `assistant_overlay.py`) bereit und leitet intern auf die neue Struktur um. Damit bleiben Build-Skripte und EXE-Konfigurationen kompatibel. Das Hilfsmodul `bootstrap.ensure_project_root()` sorgt dabei dafür, dass die Projektwurzel zuverlässig auf den `sys.path` gelegt wird (auch unter Windows-Startskripten oder PyInstaller).

## Laufzeitfluss
1. UI oder Tray erstellt einen `AssistantRouter`.
2. Der Router lädt die letzten 30 Interaktionen aus `memory.memory_db` und baut Kontext.
3. Bei neuen Fragen werden zuerst relevante Fakten via `memory.knowledge_builder` bestimmt.
4. Text- oder Vision-Anfragen laufen über `core.llm_client`, Antworten werden anschließend durch `memory.style_profile.apply_style` in den Eren-Stil übertragen.
5. Ergebnisse werden im Gedächtnis gespeichert, im Chat angezeigt und optional via `core.tts` gesprochen.

## Erweiterbarkeit
- Neue Speicherformate (z.B. Vektor-Datenbanken) können als weitere Module unter `memory/` ergänzt werden.
- Alternative Frontends (Web, CLI) verwenden weiterhin `AssistantRouter` als zentrale Schnittstelle.
- Tests können unter `tests/` abgelegt werden; Fixtures für SQLite liegen im `data/`-Verzeichnis.
