#!/usr/bin/env python3
"""
Installationsskript für EasyOCR und die benötigten Sprachmodelle.
Dieses Skript sollte in der virtuellen Umgebung ausgeführt werden.
"""

import subprocess
import sys
import os
import easyocr

def install_easyocr():
    """Installiert EasyOCR und Abhängigkeiten."""
    print("=== EasyOCR Installation ===")
    
    # Installiere EasyOCR und OpenCV
    packages = [
        "easyocr",
        "opencv-python", 
        "Pillow",
        "numpy"
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

def download_models():
    """Lädt die EasyOCR-Modelle in den Projektordner herunter."""
    print("\n=== EasyOCR Modelle Download ===")
    
    # Bestimme den Modellordner im Projekt
    project_dir = os.path.dirname(os.path.abspath(__file__))
    model_dir = os.path.join(project_dir, 'config', 'easyocr_models')
    
    # Erstelle den Ordner falls er nicht existiert
    os.makedirs(model_dir, exist_ok=True)
    print(f"Modellordner: {model_dir}")
    
    # Lösche eventuell vorhandene Modelle
    for file in os.listdir(model_dir):
        if file.endswith('.pth'):
            os.remove(os.path.join(model_dir, file))
            print(f"Alte Modelldatei gelöscht: {file}")
    
    try:
        print("Initialisiere EasyOCR Reader und lade Modelle herunter...")
        print("Dies kann einige Minuten dauern...")
        
        # Sprachenliste für deutsche, italienische, französische und englische Texte
        # 'latin' wird nicht unterstützt, verwende 'en' für lateinische Buchstaben
        languages = ['de', 'it', 'fr', 'en']
        
        # Initialisiere Reader mit Download in den Projektordner
        # Bei der ersten Initialisierung lädt EasyOCR automatisch die Modelle herunter
        reader = easyocr.Reader(
            languages,
            gpu=False,  # Keine GPU verwenden
            model_storage_directory=model_dir
        )
        
        print("✓ EasyOCR Reader erfolgreich initialisiert")
        print("✓ Modelle erfolgreich heruntergeladen")
        
        # Prüfe, welche Modelle heruntergeladen wurden
        model_files = [f for f in os.listdir(model_dir) if f.endswith('.pth')]
        print(f"Heruntergeladene Modelle ({len(model_files)}):")
        for model_file in model_files:
            print(f"  - {model_file}")
        
        return True
        
    except Exception as e:
        print(f"✗ Fehler beim Herunterladen der Modelle: {e}")
        return False

def test_installation():
    """Testet die EasyOCR-Installation."""
    print("\n=== Installation Test ===")
    
    try:
        import easyocr
        print("✓ EasyOCR Import erfolgreich")
        
        # Teste Reader-Initialisierung
        model_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config', 'easyocr_models')
        
        reader = easyocr.Reader(
            ['de', 'it', 'fr', 'en'],
            gpu=False,
            model_storage_directory=model_dir
        )
        
        print("✓ EasyOCR Reader erfolgreich initialisiert")
        print("✓ Installation vollständig und funktionsfähig")
        return True
        
    except Exception as e:
        print(f"✗ Fehler beim Testen der Installation: {e}")
        return False

def main():
    """Hauptfunktion für die Installation."""
    print("EasyOCR Installation für PDF Code Comparator")
    print("=" * 50)
    
    # Prüfe Python-Version
    if sys.version_info < (3, 7):
        print("✗ Python 3.7 oder höher erforderlich")
        return False
    
    print(f"✓ Python Version: {sys.version}")
    
    # Installiere EasyOCR
    if not install_easyocr():
        print("✗ EasyOCR Installation fehlgeschlagen")
        return False
    
    # Lade Modelle herunter
    if not download_models():
        print("✗ Modell-Download fehlgeschlagen")
        return False
    
    # Teste Installation
    if not test_installation():
        print("✗ Installationstest fehlgeschlagen")
        return False
    
    print("\n" + "=" * 50)
    print("✓ EasyOCR Installation erfolgreich abgeschlossen!")
    print("Sie können jetzt das Hauptprogramm starten mit:")
    print("python -m src.main")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)