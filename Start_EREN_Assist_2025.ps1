# EREN Assist Enhanced 2025 - PowerShell Starter
Write-Host "🚀 Starte EREN Assist Enhanced 2025..." -ForegroundColor Green
Write-Host "   Modernisiert für LangChain 2025" -ForegroundColor Cyan
Write-Host ""

# Prüfe Python
try {
    $pythonVersion = python --version 2>$null
    Write-Host "✅ Python gefunden: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python nicht gefunden! Bitte installieren Sie Python 3.8+" -ForegroundColor Red
    Read-Host "Drücken Sie Enter zum Beenden"
    exit 1
}

# Wechsle ins Scripts-Verzeichnis
Set-Location "C:\EREN_Assist\3_Scripts"

# Starte Anwendung
try {
    python eren_assist_gui_enhanced.py
    Write-Host "✅ EREN Assist erfolgreich beendet" -ForegroundColor Green
} catch {
    Write-Host "❌ Fehler beim Starten der Anwendung" -ForegroundColor Red
    Write-Host "💡 Prüfen Sie die Log-Dateien im logs\ Ordner" -ForegroundColor Yellow
}

Read-Host "Drücken Sie Enter zum Beenden"