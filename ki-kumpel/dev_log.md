# Entwicklungsnotizen

## 2025-02-14
- Analyse der bestehenden Skripte `assistant.py` und `screen_logger.py`. Beim Ausführen trat der Fehler `ModuleNotFoundError: No module named 'mss'` auf.
- Neue Hilfsfunktionen in `dependency_utils.py` eingeführt, um Pflicht- und optionale Abhängigkeiten sauber zu prüfen.
- `assistant.py` so umgebaut, dass fehlende Pakete oder ein nicht gesetzter `OPENAI_API_KEY` früh erkannt und verständlich gemeldet werden. Text-to-Speech ist nun optional.
- `screen_logger.py` erhält dieselben Prüfungen und bricht kontrolliert ab, wenn Voraussetzungen fehlen.
- `assistant_core.py` initialisiert nun den gleichen Einstiegspunkt wie `assistant.py`, damit die PyInstaller-Builds funktionieren.
<<<<<< codex/untersuche-probleme-und-erstelle-patches-80oibw

## 2025-11-13
- `python assistant.py` gestartet, um den aktuellen Einstiegspunkt zu testen. Das Skript bricht kontrolliert ab und fordert die Installation der Pakete `mss`, `Pillow` und `openai>=1.0.0` ein.
- Für Anwender dokumentiert, wie die Anwendung gestartet und welche Voraussetzungen (Python ≥3.9, virtuelle Umgebung, gesetzter `OPENAI_API_KEY`) zu beachten sind.

## 2025-11-14
- Rückmeldung vom Windows-Test: Aktivierung der virtuellen Umgebung über `.\\.venv\\Scripts\\Activate.ps1`, danach startet `python assistant.py` ohne Konsolen-Fehlerausgabe.
- `requirements.txt` ergänzt, um Installation aller Pflichtpakete mit `pip install -r requirements.txt` zu vereinfachen.
- Schritt-für-Schritt-Anleitung `docs/windows_setup.md` angelegt (PowerShell-Workflow, häufige Fehler, nächste Schritte).
- Konsolenhinweise in `assistant.py` erweitert: bei fehlenden Paketen jetzt expliziter Verweis auf `pip install -r requirements.txt` inkl. PowerShell-Kommando.
=======
>>>>>> main
