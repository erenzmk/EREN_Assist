@echo off
title EREN Assist Enhanced 2025
color 0A
cd /d "C:\EREN_Assist\3_Scripts"

echo.
echo  ███████╗██████╗ ███████╗███╗   ██╗    ██████╗  ██████╗ ██████╗ ███████╗
echo  ██╔════╝██╔══██╗██╔════╝████╗  ██║    ╚════██╗██╔═████╗╚════██╗██╔════╝
echo  █████╗  ██████╔╝█████╗  ██╔██╗ ██║     █████╔╝██║██╔██║ █████╔╝███████╗
echo  ██╔══╝  ██╔══██╗██╔══╝  ██║╚██╗██║    ██╔═══╝ ████╔╝██║██╔═══╝ ╚════██║
echo  ███████╗██║  ██║███████╗██║ ╚████║    ███████╗╚██████╔╝███████╗███████║
echo  ╚══════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═══╝    ╚══════╝ ╚═════╝ ╚══════╝╚══════╝
echo.
echo     EREN ASSIST Enhanced 2025 - KI-gestützte Datenanalyse
echo     Version: 2025.1.0 - Modernisiert für LangChain 2025
echo.
echo     Starte System...
echo.

REM Prüfe Python-Installation
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python nicht gefunden! Bitte installieren Sie Python 3.8+
    pause
    exit /b 1
)

REM Starte Anwendung
python eren_assist_gui_enhanced.py

if errorlevel 1 (
    echo.
    echo ❌ FEHLER beim Starten!
    echo 💡 Mögliche Lösungen:
    echo    • Als Administrator ausführen
    echo    • Benötigte Python-Pakete installieren
    echo    • Log-Datei in logs\ Ordner prüfen
    echo.
    pause
) else (
    echo.
    echo ✅ EREN Assist erfolgreich beendet
)