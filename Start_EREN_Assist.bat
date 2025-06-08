@echo off
title EREN Assist Enhanced
cd /d "C:\EREN_Assist\3_Scripts"

echo ================================================================
echo                    EREN ASSIST Enhanced
echo                 Starte KI-Datenanalyse System
echo ================================================================
echo.

python eren_assist_gui_enhanced.py

if errorlevel 1 (
    echo.
    echo FEHLER: Konnte nicht gestartet werden!
    pause
)