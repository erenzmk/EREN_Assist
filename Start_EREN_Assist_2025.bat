@echo off
title EREN Assist Enhanced 2025
color 0A
cls

REM ================================================================
REM     EREN ASSIST Enhanced 2025 - Moderner Starter
REM     Version: 2025.1.0
REM     Optimiert für LangChain 2025
REM ================================================================

echo.
echo  ███████╗██████╗ ███████╗███╗   ██╗    ██████╗  ██████╗ ██████╗ ███████╗
echo  ██╔════╝██╔══██╗██╔════╝████╗  ██║    ╚════██╗██╔═████╗╚════██╗██╔════╝
echo  █████╗  ██████╔╝█████╗  ██╔██╗ ██║     █████╔╝██║██╔██║ █████╔╝███████╗
echo  ██╔══╝  ██╔══██╗██╔══╝  ██║╚██╗██║    ██╔═══╝ ████╔╝██║██╔═══╝ ╚════██║
echo  ███████╗██║  ██║███████╗██║ ╚████║    ███████╗╚██████╔╝███████╗███████║
echo  ╚══════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═══╝    ╚══════╝ ╚═════╝ ╚══════╝╚══════╝
echo.
echo            EREN ASSIST Enhanced 2025 - KI-gestützte Datenanalyse
echo            Version: 2025.1.0 - Modernisiert für LangChain 2025
echo.
echo ================================================================

REM System-Checks
echo [1/4] 🔍 Prüfe System-Voraussetzungen...

REM Prüfe Python-Installation
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ FEHLER: Python nicht gefunden!
    echo.
    echo 💡 Lösung:
    echo    • Python 3.8+ von https://python.org herunterladen
    echo    • Bei Installation "Add to PATH" aktivieren
    echo    • Computer neu starten
    echo.
    pause
    exit /b 1
) else (
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
    echo ✅ Python gefunden: %PYTHON_VERSION%
)

echo [2/4] 📁 Wechsle ins Arbeitsverzeichnis...
cd /d "C:\EREN_Assist\3_Scripts"
if errorlevel 1 (
    echo ❌ FEHLER: Arbeitsverzeichnis nicht gefunden!
    echo    Erwartet: C:\EREN_Assist\3_Scripts
    echo.
    echo 💡 Lösung:
    echo    • Setup-Skript erneut ausführen
    echo    • Oder manuell Ordnerstruktur erstellen
    echo.
    pause
    exit /b 1
) else (
    echo ✅ Arbeitsverzeichnis: %CD%
)

echo [3/4] 🔎 Prüfe Hauptanwendung...
if not exist "eren_assist_gui_enhanced.py" (
    echo ❌ FEHLER: Hauptanwendung nicht gefunden!
    echo    Datei: eren_assist_gui_enhanced.py
    echo.
    echo 💡 Lösung:
    echo    • Setup-Skript erneut ausführen
    echo    • Datei aus Backup wiederherstellen
    echo.
    pause
    exit /b 1
) else (
    echo ✅ Hauptanwendung gefunden
)

echo [4/4] 🚀 Starte EREN Assist Enhanced...
echo.
echo ================================================================
echo                    SYSTEM WIRD GESTARTET
echo ================================================================
echo.

REM Starte die Anwendung
python eren_assist_gui_enhanced.py

REM Prüfe Exit-Code der Anwendung
if errorlevel 1 (
    echo.
    echo ================================================================
    echo                     ❌ FEHLER AUFGETRETEN
    echo ================================================================
    echo.
    echo 🔍 Mögliche Ursachen:
    echo    • Fehlende Python-Pakete
    echo    • Berechtigungsprobleme
    echo    • Beschädigte Dateien
    echo.
    echo 💡 Lösungsvorschläge:
    echo    1. Als Administrator ausführen
    echo    2. Python-Pakete installieren:
    echo       pip install langchain-community gpt4all
    echo    3. Log-Dateien prüfen:
    echo       C:\EREN_Assist\logs\
    echo    4. System-Check in der Anwendung ausführen
    echo.
    echo 📞 Support:
    echo    • Log-Dateien sammeln
    echo    • Fehlermeldung notieren
    echo    • System-Informationen bereithalten
    echo.
    set /p dummy="Drücken Sie Enter zum Beenden..."
) else (
    echo.
    echo ================================================================
    echo                ✅ EREN ASSIST ERFOLGREICH BEENDET
    echo ================================================================
    echo.
    echo 📊 Session abgeschlossen
    echo 💾 Daten wurden gespeichert
    echo 📋 Logs wurden aktualisiert
    echo.
    echo Vielen Dank für die Nutzung von EREN Assist Enhanced 2025!
    echo.
    timeout /t 3 /nobreak >nul
)

REM Bereinigung
set PYTHON_VERSION=
set dummy=

exit /b 0