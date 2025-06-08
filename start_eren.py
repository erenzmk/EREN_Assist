#!/usr/bin/env python3
"""
EREN Assist 2025 - Python Starter
Direkter Start mit integrierter Fehlerprüfung
"""

import sys
import os
from pathlib import Path

def main():
    print("🚀 EREN Assist 2025 - Python Starter")
    print("=" * 50)
    
    # Prüfe Python-Version
    if sys.version_info < (3, 8):
        print(f"❌ Python 3.8+ erforderlich, gefunden: {sys.version_info.major}.{sys.version_info.minor}")
        input("Drücken Sie Enter zum Beenden...")
        return
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} OK")
    
    # Wechsle ins Scripts-Verzeichnis
    scripts_dir = Path(__file__).parent / "3_Scripts"
    main_script = scripts_dir / "eren_assist_gui_enhanced.py"
    
    if not main_script.exists():
        print(f"❌ Hauptskript nicht gefunden: {main_script}")
        input("Drücken Sie Enter zum Beenden...")
        return
    
    print(f"✅ Hauptskript gefunden")
    print("🔄 Starte EREN Assist Enhanced...")
    print()
    
    # Starte Hauptanwendung
    os.chdir(scripts_dir)
    
    try:
        import subprocess
        result = subprocess.run([sys.executable, "eren_assist_gui_enhanced.py"], check=True)
        print("✅ EREN Assist erfolgreich beendet")
    except subprocess.CalledProcessError as e:
        print(f"❌ Fehler beim Starten: {e}")
        print("💡 Prüfen Sie die Log-Dateien im logs/ Ordner")
    except Exception as e:
        print(f"❌ Unerwarteter Fehler: {e}")
    
    input("Drücken Sie Enter zum Beenden...")

if __name__ == "__main__":
    main()