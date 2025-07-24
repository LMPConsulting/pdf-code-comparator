#!/usr/bin/env python3
"""
Installationsskript für erweiterte OCR-Abhängigkeiten.
Installiert OpenCV und PIL für bessere Bildverarbeitung.
"""

import subprocess
import sys
import os

def install_enhanced_ocr_dependencies():
    """Installiert alle Abhängigkeiten für erweiterte OCR."""
    print("=== Erweiterte OCR Abhängigkeiten Installation ===")
    
    packages = [
        "opencv-python",
        "Pillow",
        "numpy",
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

def test_enhanced_ocr():
    """Testet alle OCR-Abhängigkeiten."""
    print("\n=== Test der erweiterten OCR ===")
    
    try:
        # Teste OpenCV
        import cv2
        print(f"✓ OpenCV verfügbar: {cv2.__version__}")
        
        # Teste PIL
        from PIL import Image, ImageEnhance
        print("✓ PIL/Pillow verfügbar")
        
        # Teste NumPy
        import numpy as np
        print(f"✓ NumPy verfügbar: {np.__version__}")
        
        # Teste PyMuPDF
        import fitz
        print(f"✓ PyMuPDF verfügbar: {fitz.version}")
        
        # Teste Tesseract
        result = subprocess.run(['tesseract', '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"✓ Tesseract gefunden: {version_line}")
        else:
            print("✗ Tesseract nicht gefunden")
            return False
        
        print("✓ Alle Abhängigkeiten für erweiterte OCR verfügbar")
        return True
        
    except Exception as e:
        print(f"✗ Fehler beim Testen: {e}")
        return False

def main():
    """Hauptfunktion für die Installation."""
    print("Erweiterte OCR Installation für PDF Code Comparator")
    print("=" * 55)
    
    # Prüfe Python-Version
    if sys.version_info < (3, 7):
        print("✗ Python 3.7 oder höher erforderlich")
        return False
    
    print(f"✓ Python Version: {sys.version}")
    
    # Installiere Abhängigkeiten
    if not install_enhanced_ocr_dependencies():
        print("✗ Installation fehlgeschlagen")
        return False
    
    # Teste Installation
    if not test_enhanced_ocr():
        print("✗ Test fehlgeschlagen")
        return False
    
    print("\n" + "=" * 55)
    print("✓ Erweiterte OCR Installation erfolgreich!")
    print("Das System nutzt jetzt:")
    print("- Erweiterte Bildverbesserung mit OpenCV")
    print("- Kontrast- und Schärfeverbesserung mit PIL")
    print("- Rauschreduktion und adaptive Binarisierung")
    print("- Optimierte Tesseract-Parameter")
    print("\nSie können jetzt das Hauptprogramm starten mit:")
    print("python -m src.main")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)