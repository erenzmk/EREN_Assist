@echo off
title EREN Assist Enhanced
color 0A
cd /d "C:\EREN_Assist\3_Scripts"

echo.
echo  ███████╗██████╗ ███████╗███╗   ██╗
echo  ██╔════╝██╔══██╗██╔════╝████╗  ██║
echo  █████╗  ██████╔╝█████╗  ██╔██╗ ██║
echo  ██╔══╝  ██╔══██╗██╔══╝  ██║╚██╗██║
echo  ███████╗██║  ██║███████╗██║ ╚████║
echo  ╚══════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═══╝
echo.
echo     EREN ASSIST Enhanced
echo     Starte System...
echo.

python eren_assist_gui_enhanced.py

if errorlevel 1 (
    echo.
    echo Fehler beim Starten! Druecke eine Taste...
    pause
)