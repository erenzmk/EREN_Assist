# Entwicklungsnotizen

## 2025-02-14
- Analyse der bestehenden Skripte `assistant.py` und `screen_logger.py`. Beim Ausführen trat der Fehler `ModuleNotFoundError: No module named 'mss'` auf.
- Neue Hilfsfunktionen in `dependency_utils.py` eingeführt, um Pflicht- und optionale Abhängigkeiten sauber zu prüfen.
- `assistant.py` so umgebaut, dass fehlende Pakete oder ein nicht gesetzter `OPENAI_API_KEY` früh erkannt und verständlich gemeldet werden. Text-to-Speech ist nun optional.
- `screen_logger.py` erhält dieselben Prüfungen und bricht kontrolliert ab, wenn Voraussetzungen fehlen.
- `assistant_core.py` initialisiert nun den gleichen Einstiegspunkt wie `assistant.py`, damit die PyInstaller-Builds funktionieren.
