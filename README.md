# Konfiguration

## Dateien in diesem Ordner

### settings.ini
Hauptkonfigurationsdatei für die Anwendung. Kopieren Sie `settings_example.ini` und passen Sie die Pfade an Ihr System an.

### master_codes.xlsx (NICHT IM REPOSITORY)
**Diese Datei müssen Sie selbst erstellen!**

Die Master-Codeliste ist zu groß für GitHub (>25MB) und wird daher nicht mit hochgeladen.

#### Struktur der master_codes.xlsx:
- **Spalte A**: Code (z.B. A86, B8A, I46, etc.)
- **Keine Überschriften nötig**
- **Ein Code pro Zeile**

#### Beispiel-Inhalt:
```
A86
B8A
C3Z
E2F
I46
I23
Z75
...
```

#### So erstellen Sie die Datei:
1. Öffnen Sie Excel oder LibreOffice Calc
2. Geben Sie alle Ihre gültigen Codes in Spalte A ein
3. Speichern Sie als `master_codes.xlsx` in diesem Ordner
4. Die Anwendung lädt diese Datei automatisch beim Start

### easyocr_models/ (NICHT IM REPOSITORY)
Dieser Ordner enthält die EasyOCR-Modelle und wird automatisch beim ersten Start erstellt.

## Erste Einrichtung

1. Kopieren Sie `settings_example.ini` zu `settings.ini`
2. Passen Sie den Tesseract-Pfad in `settings.ini` an
3. Erstellen Sie `master_codes.xlsx` mit Ihren Codes
4. Führen Sie `python install_easyocr.py` aus