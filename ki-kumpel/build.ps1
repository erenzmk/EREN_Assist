Write-Host "=== KI-Kumpel Build Script gestartet ==="

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
Write-Host "Projektpfad: $projectRoot"
Set-Location $projectRoot

if (-Not (Test-Path ".\.venv")) {
    Write-Host "Kein .venv gefunden – erstelle neues virtuelles Environment..."
    python -m venv .venv
}

Write-Host "Aktiviere Virtual Environment..."
. .\.venv\Scripts\Activate.ps1

Write-Host "Installiere Dependencies..."
pip install -r requirements.txt

Write-Host "Lösche alte Build-Ordner..."
Remove-Item -Recurse -Force dist -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force build -ErrorAction SilentlyContinue

Write-Host "Beende alte Prozesse..."
taskkill /IM ki_kumpel_app.exe /F -ErrorAction SilentlyContinue
taskkill /IM assistant_tray.exe /F -ErrorAction SilentlyContinue

Write-Host "Starte PyInstaller Build..."
pyinstaller --clean --onefile --noconsole --add-data "assets\ChatGPT.ico;assets" --icon assets\ChatGPT.ico src\ki_kumpel_app.py

Write-Host "Build abgeschlossen!"

if (Test-Path ".\dist\ki_kumpel_app.exe") {
    Write-Host "Starte KI-Kumpel..."
    Start-Process ".\dist\ki_kumpel_app.exe"
} else {
    Write-Host "Fehler: EXE wurde nicht gefunden!"
}

Write-Host "=== Fertig ==="
