# Windows-Setup für den KI-Kumpel

Diese Anleitung führt dich Schritt für Schritt durch die Einrichtung unter Windows (PowerShell). Alle Befehle sind so formuliert, dass du sie direkt kopieren kannst.

## 1. Repository aktualisieren
```powershell
cd $HOME\Documents\GitHub\EREN_Assist\ki-kumpel
git pull
```

## 2. Virtuelle Umgebung anlegen und aktivieren
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
> **Hinweis:** In PowerShell gibt es kein `&&`. Befehle werden nacheinander ausgeführt.

## 3. Abhängigkeiten installieren
```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

Falls du die Sprach-Ausgabe nutzen möchtest, bleibt `pyttsx3` in der `requirements.txt` stehen und wird automatisch mit installiert.

## 4. OpenAI-API-Key setzen (nur einmal pro Terminal nötig)
```powershell
$env:OPENAI_API_KEY = "DEIN_API_KEY"
```

Optional kannst du den Key dauerhaft in deinem Benutzerprofil speichern:
```powershell
[Environment]::SetEnvironmentVariable("OPENAI_API_KEY", "DEIN_API_KEY", "User")
```

## 5. Anwendung starten
```powershell
python assistant.py
```

Sobald die Abhängigkeiten vorhanden sind und der API-Key gesetzt ist, startet das Overlay-Fenster. Die KI beschreibt deinen Bildschirm alle `CAPTURE_INTERVAL` Sekunden (Standard: 120 Sekunden) und schreibt alles nach `activity_log.txt`.

## 6. Screen-Logger separat starten (optional)
```powershell
python screen_logger.py
```

## 7. Häufige Fehler
| Problem | Ursache | Lösung |
| --- | --- | --- |
| `Fehlende Python-Pakete: ...` | Pakete noch nicht installiert | `pip install -r requirements.txt` ausführen |
| `OPENAI_API_KEY ist nicht gesetzt` | Umgebungsvariable fehlt | Schritt 4 wiederholen |
| `Das Skript beendet sich sofort ohne Ausgabe` | Virtuelle Umgebung nicht aktiv oder Pakete fehlen | `.\.venv\Scripts\Activate.ps1` ausführen und Schritt 3 wiederholen |

## 8. Nächste Schritte
- Nach jedem Arbeitstag `activity_log.txt` prüfen – dort steht jede Analyse der KI.
- Über den Button **📝 Tag zusammenfassen** erhältst du direkt im Overlay eine Zusammenfassung.
- Für den späteren EXE-Build kannst du mit `pyinstaller assistant.py` starten; die Abhängigkeiten werden aus der virtuellen Umgebung übernommen.

Alles, was du hier tust, solltest du nach jedem Durchlauf in `dev_log.md` dokumentieren, damit wir den Verlauf nachvollziehen können.
