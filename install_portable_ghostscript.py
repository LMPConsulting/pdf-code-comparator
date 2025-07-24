#!/usr/bin/env python3
"""
Portable Ghostscript Installation ohne Admin-Rechte.
Lädt eine portable Version von Ghostscript herunter und konfiguriert sie.
"""

import subprocess
import sys
import os
import urllib.request
import zipfile
import shutil

def download_portable_ghostscript():
    """Lädt portable Ghostscript-Version herunter."""
    print("=== Portable Ghostscript Installation ===")
    
    # Portable Ghostscript Download (ohne Installer)
    gs_url = "https://github.com/ArtifexSoftware/ghostpdl-downloads/releases/download/gs10031/gs10031w64.zip"
    gs_zip = "ghostscript_portable.zip"
    gs_dir = "ghostscript"
    
    try:
        print("Lade portable Ghostscript herunter...")
        urllib.request.urlretrieve(gs_url, gs_zip)
        print("✓ Ghostscript heruntergeladen")
        
        # Entpacke Ghostscript
        print("Entpacke Ghostscript...")
        with zipfile.ZipFile(gs_zip, 'r') as zip_ref:
            zip_ref.extractall(gs_dir)
        
        # Finde die Ghostscript-Executable
        gs_exe = None
        for root, dirs, files in os.walk(gs_dir):
            for file in files:
                if file in ['gswin64c.exe', 'gs.exe']:
                    gs_exe = os.path.join(root, file)
                    break
            if gs_exe:
                break
        
        if gs_exe:
            gs_exe = os.path.abspath(gs_exe)
            print(f"✓ Ghostscript gefunden: {gs_exe}")
            
            # Teste Ghostscript
            result = subprocess.run([gs_exe, '--version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✓ Ghostscript funktionsfähig: {result.stdout.strip()}")
                return gs_exe
            else:
                print("✗ Ghostscript Test fehlgeschlagen")
                return None
        else:
            print("✗ Ghostscript Executable nicht gefunden")
            return None
            
    except Exception as e:
        print(f"✗ Fehler bei Ghostscript Installation: {e}")
        return None
    finally:
        # Lösche ZIP-Datei
        if os.path.exists(gs_zip):
            os.remove(gs_zip)

def install_ocrmypdf():
    """Installiert OCRmyPDF."""
    print("\n=== OCRmyPDF Installation ===")
    
    packages = [
        "ocrmypdf",
        "PyMuPDF",
        "pandas", 
        "openpyxl"
    ]
    
    for package in packages:
        print(f"Installiere {package}...")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", 
                "--no-cache-dir", package
            ])
            print(f"✓ {package} erfolgreich installiert")
        except subprocess.CalledProcessError as e:
            print(f"✗ Fehler beim Installieren von {package}: {e}")
            return False
    
    return True

def create_ghostscript_config(gs_exe_path):
    """Erstellt eine Konfigurationsdatei für Ghostscript."""
    config_content = f"""# Ghostscript Konfiguration für OCRmyPDF
# Portable Ghostscript Pfad
GHOSTSCRIPT_PATH = "{gs_exe_path}"
"""
    
    with open("ghostscript_config.py", "w") as f:
        f.write(config_content)
    
    print(f"✓ Ghostscript Konfiguration erstellt: ghostscript_config.py")

def test_ocrmypdf_with_portable_gs(gs_exe_path):
    """Testet OCRmyPDF mit portable Ghostscript."""
    print("\n=== OCRmyPDF Test mit portable Ghostscript ===")
    
    try:
        # Setze Ghostscript-Pfad in Umgebungsvariable
        os.environ['GS'] = gs_exe_path
        
        # Teste OCRmyPDF Import
        import ocrmypdf
        print("✓ OCRmyPDF Import erfolgreich")
        
        # Teste Tesseract
        result = subprocess.run(['tesseract', '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"✓ Tesseract gefunden: {version_line}")
        else:
            print("✗ Tesseract nicht gefunden")
            return False
        
        print("✓ OCRmyPDF mit portable Ghostscript konfiguriert")
        return True
        
    except Exception as e:
        print(f"✗ Fehler beim Testen: {e}")
        return False

def main():
    """Hauptfunktion für die portable Installation."""
    print("Portable Ghostscript & OCRmyPDF Installation")
    print("=" * 50)
    
    # Installiere portable Ghostscript
    gs_exe_path = download_portable_ghostscript()
    if not gs_exe_path:
        print("✗ Portable Ghostscript Installation fehlgeschlagen")
        return False
    
    # Installiere OCRmyPDF
    if not install_ocrmypdf():
        print("✗ OCRmyPDF Installation fehlgeschlagen")
        return False
    
    # Erstelle Konfiguration
    create_ghostscript_config(gs_exe_path)
    
    # Teste Installation
    if not test_ocrmypdf_with_portable_gs(gs_exe_path):
        print("✗ OCRmyPDF Test fehlgeschlagen")
        return False
    
    print("\n" + "=" * 50)
    print("✓ Portable Ghostscript & OCRmyPDF Installation erfolgreich!")
    print(f"Ghostscript Pfad: {gs_exe_path}")
    print("Sie können jetzt das Hauptprogramm starten mit:")
    print("python -m src.main")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)