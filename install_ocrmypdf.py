#!/usr/bin/env python3
"""
Installationsskript für OCRmyPDF.
Dieses Skript sollte in der virtuellen Umgebung ausgeführt werden.
"""

import subprocess
import sys
import os

def install_ocrmypdf():
    """Installiert OCRmyPDF und Abhängigkeiten."""
    print("=== OCRmyPDF Installation ===")
    
    # Installiere OCRmyPDF
    packages = [
        "ocrmypdf",
        "PyMuPDF",  # fitz
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

def test_installation():
    """Testet die OCRmyPDF-Installation."""
    print("\n=== Installation Test ===")
    
    try:
        import ocrmypdf
        print("✓ OCRmyPDF Import erfolgreich")
        
        # Teste Tesseract-Verfügbarkeit
        result = subprocess.run([
            sys.executable, "-c", 
            "import ocrmypdf; print('OCRmyPDF Version:', ocrmypdf.__version__)"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ OCRmyPDF funktionsfähig")
            print(result.stdout.strip())
        else:
            print("✗ OCRmyPDF Test fehlgeschlagen")
            print(result.stderr)
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Fehler beim Testen der Installation: {e}")
        return False

def main():
    """Hauptfunktion für die Installation."""
    print("OCRmyPDF Installation für PDF Code Comparator")
    print("=" * 50)
    
    # Prüfe Python-Version
    if sys.version_info < (3, 7):
        print("✗ Python 3.7 oder höher erforderlich")
        return False
    
    print(f"✓ Python Version: {sys.version}")
    
    # Installiere OCRmyPDF
    if not install_ocrmypdf():
        print("✗ OCRmyPDF Installation fehlgeschlagen")
        return False
    
    # Teste Installation
    if not test_installation():
        print("✗ Installationstest fehlgeschlagen")
        return False
    
    print("\n" + "=" * 50)
    print("✓ OCRmyPDF Installation erfolgreich abgeschlossen!")
    print("Sie können jetzt das Hauptprogramm starten mit:")
    print("python -m src.main")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)