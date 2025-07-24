# Contributing to PDF Code Comparator

## Entwicklungsumgebung einrichten

1. Repository klonen:
```bash
git clone <repository-url>
cd pdf-code-comparator
```

2. Virtual Environment erstellen:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# oder
venv\Scripts\activate     # Windows
```

3. Dependencies installieren:
```bash
pip install -r requirements.txt
```

4. Tesseract OCR installieren:
```bash
python install_ocrmypdf.py
```

## Code-Struktur

### Hauptmodule

- **`src/main.py`**: GUI-Anwendung und Haupteinstiegspunkt
- **`src/core.py`**: Kern-Logik für OCR-Verarbeitung und Code-Vergleich
- **`src/gui.py`**: Tkinter-basierte Benutzeroberfläche
- **`src/config.py`**: Konfigurationsverwaltung
- **`src/reporting.py`**: Excel-Report-Generierung
- **`src/ocr_correction.py`**: OCR-Korrektur-Algorithmen
- **`src/code_filters.py`**: Code-Filterung und Kategorisierung

### Wichtige Funktionen

#### OCR-Verarbeitung (`src/core.py`)
- `extract_codes()`: Hauptfunktion für Code-Extraktion
- `clean_code_advanced()`: Erweiterte OCR-Korrektur
- `compare_codes_with_correction()`: Code-Vergleich mit Korrektur

#### Wahrscheinlichkeits-System
- `calculate_precise_probability()`: Präzise Wahrscheinlichkeits-Berechnung
- `generate_korrekturmatch_comment()`: Kommentar-Generierung für Matches

## Testing

```bash
# Basis-Test
python test_easyocr_setup.py

# Manuelle Tests mit GUI
python -m src.main
```

## Code-Style

- Verwenden Sie aussagekräftige Variablennamen
- Dokumentieren Sie komplexe Funktionen
- Folgen Sie PEP 8 Richtlinien
- Verwenden Sie Type Hints wo möglich

## Performance-Überlegungen

- OCR-Verarbeitung ist ressourcenintensiv
- Verwenden Sie frühzeitige Beendigung bei erfolgreichen Matches
- Begrenzen Sie die Anzahl der OCR-Versuche
- Optimieren Sie Bildauflösung für Balance zwischen Qualität und Geschwindigkeit

## Debugging

### OCR-Debug-Ausgaben
Das System erstellt Debug-Dateien in `debug_ocr_text/` für detaillierte Analyse.

### Logging
Verwenden Sie `print()` Statements für wichtige Verarbeitungsschritte.

### Häufige Probleme

1. **Tesseract nicht gefunden**: Prüfen Sie den Pfad in `config/settings.ini`
2. **EasyOCR Modelle fehlen**: Führen Sie `install_easyocr.py` aus
3. **Ghostscript Fehler**: Installieren Sie Ghostscript für OCRmyPDF

## Neue Features hinzufügen

1. Erstellen Sie einen Feature-Branch
2. Implementieren Sie die Änderungen
3. Testen Sie gründlich mit verschiedenen PDF-Typen
4. Dokumentieren Sie neue Funktionen
5. Erstellen Sie einen Pull Request

## Bekannte Limitierungen

- Funktioniert am besten mit deutschsprachigen PDFs
- Erfordert Master-Codeliste für Validierung
- Performance abhängig von PDF-Qualität und -Größe