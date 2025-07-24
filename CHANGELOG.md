# Changelog

Alle wichtigen Änderungen an diesem Projekt werden in dieser Datei dokumentiert.

## [1.0.0] - 2024-01-XX

### Hinzugefügt
- **Multi-OCR-System**: Integration von EasyOCR, Tesseract und OCRmyPDF
- **Intelligente OCR-Korrektur**: Automatische Korrektur häufiger OCR-Fehler
- **Präzises Wahrscheinlichkeitssystem**: 40% Basis + Kontext-Validierung
- **Steuer-Code-Behandlung**: Spezielle Behandlung für I-Codes
- **Korrekturmatch-Klassifikation**: Unterscheidung zwischen direkten Matches und Korrekturmatches
- **Erweiterte Excel-Reports**: Farbkodierung und detaillierte Kommentare
- **Performance-Optimierungen**: 91% weniger OCR-Versuche
- **GUI-Anwendung**: Benutzerfreundliche Tkinter-Oberfläche

### OCR-Korrekturen
- **Zeichenersetzung**: B↔8, I↔1↔L, 0↔O, 5↔S, 6↔G, 2↔Z
- **0-Entfernung**: Entfernt fälschlich eingefügte "0" an zweiter Stelle
- **Leerzeichen-Bereinigung**: Entfernt störende Leerzeichen
- **Systematische Permutation**: Alle möglichen Korrektur-Kombinationen

### Wahrscheinlichkeitssystem
- **Basis-Wahrscheinlichkeit**: 40% pro PDF für Fund in Master-Liste
- **Korrektur-Abzüge**: -10% pro durchgeführter Korrektur
- **Kontext-Bonus**: Variable Gewichtung für Nachbar-Codes
- **Intelligente Gewichtung**: Unterschiedliche Bonus-Systeme je nach Korrektur-Typ

### Match-Klassifikation
- **Direkter Match**: Code ohne Korrekturen in Master-Liste gefunden
- **Korrekturmatch**: Code nach Korrekturen in Master-Liste gefunden
- **Kontext-Validierung**: 1 Code bei direkten Matches, 3 Codes bei Korrekturen

### Steuer-Codes (I-Codes)
- **Automatische Erkennung**: Codes mit Prefix "I"
- **Grau-Markierung**: Spezielle Farbkodierung in Reports
- **Prioritäts-Anzeige**: Erscheinen ganz oben in Ergebnisliste
- **Gleiche Bewertung**: Identisches Wahrscheinlichkeitssystem

### Performance
- **OCR-Optimierung**: Von 81 auf maximal 7 Versuche pro Seite
- **DPI-Optimierung**: 300 DPI statt 600 DPI für bessere Performance
- **Timeout-Optimierung**: 10 Sekunden statt 30 Sekunden pro Versuch
- **Frühzeitige Beendigung**: Stop bei erfolgreichen Matches

### Farbkodierung
- **Dunkel Grün**: 100% Sicherheit
- **Helles Grün**: 99-90% Sicherheit
- **Dunkles Gelb**: 89-80% Sicherheit
- **Helles Gelb**: 79-60% Sicherheit
- **Orange**: <60% Sicherheit
- **Rot**: Nur in einem PDF gefunden
- **Grau**: Steuer-Codes

## [Geplant für zukünftige Versionen]

### [1.1.0] - Geplant
- **Batch-Verarbeitung**: Mehrere PDF-Paare gleichzeitig verarbeiten
- **API-Interface**: REST-API für externe Integration
- **Erweiterte Statistiken**: Detaillierte Analyse-Reports
- **Custom OCR-Modelle**: Trainierbare Modelle für spezifische Dokument-Typen

### [1.2.0] - Geplant
- **Cloud-Integration**: Azure/AWS OCR-Services
- **Machine Learning**: Automatische Verbesserung der Korrektur-Algorithmen
- **Multi-Language**: Unterstützung für weitere Sprachen
- **Web-Interface**: Browser-basierte Benutzeroberfläche