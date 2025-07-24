#!/usr/bin/env python3
"""
Installationsskript für Ghostscript und OCRmyPDF.
Dieses Skript installiert alle benötigten Abhängigkeiten für OCRmyPDF.
"""

import subprocess
import sys
import os
import urllib.request
import zipfile
import shutil

def download_and_install_ghostscript():
    """Lädt Ghostscript herunter und installiert es."""
    print("=== Ghostscript Installation ===")
    
    # Ghostscript Download URL für Windows 64-bit
    gs_url = "https://github.com/ArtifexSoftware/ghostpdl-downloads/releases/download/gs10031/gs10031w64.exe"
    gs_installer = "gs_installer.exe"
    
    try:
        print("Lade Ghostscript herunter...")
        urllib.request.urlretrieve(gs_url, gs_installer)
        print("✓ Ghostscript heruntergeladen")
        
        print("Starte Ghostscript Installation...")
        print("WICHTIG: Installieren Sie Ghostscript in den Standard-Pfad!")
        
        # Starte Installer
        result = subprocess.run([gs_installer], check=False)
        
        if result.returncode == 0:
            print("✓ Ghostscript Installation abgeschlossen")
            
            # Füge Ghostscript zum PATH hinzu
            gs_path = r"C:\Program Files\gs\gs10.03.1\bin"
            if os.path.exists(gs_path):
                current_path = os.environ.get('PATH', '')
                if gs_path not in current_path:
                    os.environ['PATH'] = gs_path + os.pathsep + current_path
                    print(f"✓ Ghostscript zum PATH hinzugefügt: {gs_path}")
                return True
            else:
                print("⚠ Ghostscript installiert, aber Pfad nicht gefunden. Bitte manuell zum PATH hinzufügen.")
                return True
        else:
            print("✗ Ghostscript Installation fehlgeschlagen")
            return False
            
    except Exception as e:
        print(f"✗ Fehler bei Ghostscript Installation: {e}")
        return False
    finally:
        # Lösche Installer
        if os.path.exists(gs_installer):
            os.remove(gs_installer)

def install_ocrmypdf():
    """Installiert OCRmyPDF und Abhängigkeiten."""
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

def test_ocrmypdf():
    """Testet OCRmyPDF mit allen Abhängigkeiten."""
    print("\n=== OCRmyPDF Test ===")
    
    try:
        # Teste OCRmyPDF Import
        import ocrmypdf
        print("✓ OCRmyPDF Import erfolgreich")
        
        # Teste Ghostscript
        result = subprocess.run(['gswin64c', '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ Ghostscript gefunden: {result.stdout.strip()}")
        else:
            print("✗ Ghostscript nicht im PATH gefunden")
            return False
        
        # Teste Tesseract
        result = subprocess.run(['tesseract', '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"✓ Tesseract gefunden: {version_line}")
        else:
            print("✗ Tesseract nicht gefunden")
            return False
        
        print("✓ Alle OCRmyPDF Abhängigkeiten verfügbar")
        return True
        
    except Exception as e:
        print(f"✗ Fehler beim Testen: {e}")
        return False

def main():
    """Hauptfunktion für die Installation."""
    print("Ghostscript & OCRmyPDF Installation für PDF Code Comparator")
    print("=" * 60)
    
    # Prüfe ob Ghostscript bereits installiert ist
    try:
        result = subprocess.run(['gswin64c', '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ Ghostscript bereits installiert")
            gs_installed = True
        else:
            gs_installed = False
    except:
        gs_installed = False
    
    # Installiere Ghostscript falls nötig
    if not gs_installed:
        if not download_and_install_ghostscript():
            print("✗ Ghostscript Installation fehlgeschlagen")
            return False
    
    # Installiere OCRmyPDF
    if not install_ocrmypdf():
        print("✗ OCRmyPDF Installation fehlgeschlagen")
        return False
    
    # Teste Installation
    if not test_ocrmypdf():
        print("✗ OCRmyPDF Test fehlgeschlagen")
        return False
    
    print("\n" + "=" * 60)
    print("✓ Ghostscript & OCRmyPDF Installation erfolgreich!")
    print("Sie können jetzt das Hauptprogramm starten mit:")
    print("python -m src.main")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)