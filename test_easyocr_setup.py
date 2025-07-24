#!/usr/bin/env python3
"""
Test-Skript für die EasyOCR-Integration im PDF Code Comparator.
Testet die Konfiguration und Initialisierung ohne GUI.
"""

import os
import sys

def test_imports():
    """Testet, ob alle benötigten Module importiert werden können."""
    print("=== Import Tests ===")
    
    try:
        import easyocr
        print("✓ easyocr importiert")
    except ImportError as e:
        print(f"✗ easyocr Import fehlgeschlagen: {e}")
        return False
    
    try:
        import cv2
        print("✓ opencv-python importiert")
    except ImportError as e:
        print(f"✗ opencv-python Import fehlgeschlagen: {e}")
        return False
    
    try:
        import numpy as np
        print("✓ numpy importiert")
    except ImportError as e:
        print(f"✗ numpy Import fehlgeschlagen: {e}")
        return False
    
    try:
        from PIL import Image
        print("✓ Pillow importiert")
    except ImportError as e:
        print(f"✗ Pillow Import fehlgeschlagen: {e}")
        return False
    
    try:
        import fitz
        print("✓ PyMuPDF importiert")
    except ImportError as e:
        print(f"✗ PyMuPDF Import fehlgeschlagen: {e}")
        return False
    
    return True

def test_config():
    """Testet die Konfiguration."""
    print("\n=== Konfiguration Tests ===")
    
    try:
        from src import config
        app_config = config.load_config()
        
        if not app_config or not app_config.sections():
            print("✗ Konfiguration leer oder nicht gefunden")
            return False
        
        print("✓ settings.ini geladen")
        
        # Teste EasyOCR Modellordner
        easyocr_model_dir = app_config.get('General', 'easyocr_model_dir', fallback='easyocr_models')
        full_model_dir = os.path.join(config.get_base_path(), 'config', easyocr_model_dir)
        
        if not os.path.exists(full_model_dir):
            print(f"✗ EasyOCR Modellordner nicht gefunden: {full_model_dir}")
            return False
        
        print(f"✓ EasyOCR Modellordner gefunden: {full_model_dir}")
        
        # Prüfe Modell-Dateien
        model_files = [f for f in os.listdir(full_model_dir) if f.endswith('.pth')]
        if not model_files:
            print("✗ Keine EasyOCR Modell-Dateien (.pth) gefunden")
            return False
        
        print(f"✓ {len(model_files)} Modell-Dateien gefunden")
        for model_file in model_files:
            print(f"  - {model_file}")
        
        # Teste Master Codes
        master_codes = config.load_master_codes(app_config)
        if not master_codes:
            print("⚠ Master Codes Liste ist leer (Warnung, aber nicht kritisch)")
        else:
            print(f"✓ {len(master_codes)} Master Codes geladen")
        
        return True
        
    except Exception as e:
        print(f"✗ Konfigurationstest fehlgeschlagen: {e}")
        return False

def test_easyocr_init():
    """Testet die EasyOCR-Initialisierung."""
    print("\n=== EasyOCR Initialisierung Test ===")
    
    try:
        import easyocr
        from src import config
        
        app_config = config.load_config()
        easyocr_model_dir = app_config.get('General', 'easyocr_model_dir', fallback='easyocr_models')
        full_model_dir = os.path.join(config.get_base_path(), 'config', easyocr_model_dir)
        
        print("Initialisiere EasyOCR Reader...")
        print("(Dies kann 30-60 Sekunden dauern...)")
        
        reader = easyocr.Reader(
            ['de', 'it', 'fr', 'en'],
            gpu=False,
            model_storage_directory=full_model_dir
        )
        
        print("✓ EasyOCR Reader erfolgreich initialisiert")
        
        # Teste Allowlist
        allowlist = app_config.get('Codes', 'easyocr_allowlist', fallback='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
        print(f"✓ Allowlist konfiguriert: {allowlist}")
        
        return True
        
    except Exception as e:
        print(f"✗ EasyOCR Initialisierung fehlgeschlagen: {e}")
        return False

def test_core_functions():
    """Testet die Core-Funktionen."""
    print("\n=== Core Funktionen Test ===")
    
    try:
        from src import core
        
        # Teste clean_code Funktion
        test_codes = ['A1A', 'A01X', 'B2A', 'P0B', 'XYZ']
        print("Teste clean_code Funktion:")
        for code in test_codes:
            cleaned = core.clean_code(code, None)  # Keine Master-Validierung im Test
            print(f"  '{code}' -> '{cleaned}'")
        
        print("✓ clean_code Funktion funktioniert")
        
        # Teste compare_codes Funktion
        codes1 = {'A1A', 'B2A', 'XYZ'}
        codes2 = {'A1A', 'C3B', 'XYZ'}
        in_both, only1, only2 = core.compare_codes(codes1, codes2)
        
        print(f"✓ compare_codes Funktion funktioniert")
        print(f"  Test: {codes1} vs {codes2}")
        print(f"  In beiden: {in_both}")
        print(f"  Nur in 1: {only1}")
        print(f"  Nur in 2: {only2}")
        
        return True
        
    except Exception as e:
        print(f"✗ Core Funktionen Test fehlgeschlagen: {e}")
        return False

def main():
    """Hauptfunktion für alle Tests."""
    print("PDF Code Comparator - EasyOCR Setup Test")
    print("=" * 50)
    
    all_passed = True
    
    # Führe alle Tests durch
    tests = [
        ("Imports", test_imports),
        ("Konfiguration", test_config),
        ("EasyOCR Initialisierung", test_easyocr_init),
        ("Core Funktionen", test_core_functions)
    ]
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        if not test_func():
            all_passed = False
            print(f"✗ {test_name} fehlgeschlagen")
        else:
            print(f"✓ {test_name} erfolgreich")
    
    print("\n" + "=" * 50)
    if all_passed:
        print("✓ Alle Tests erfolgreich!")
        print("Das Programm sollte jetzt funktionieren.")
        print("Starten Sie es mit: python -m src.main")
    else:
        print("✗ Einige Tests sind fehlgeschlagen.")
        print("Bitte beheben Sie die Probleme vor dem Start des Hauptprogramms.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)