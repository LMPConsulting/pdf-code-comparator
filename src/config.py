# src/config.py
import configparser
import os
import sys
import pandas as pd # NEU: Für das Lesen der Excel-Masterliste

def get_base_path():
    """Hilfsfunktion, um den Basis-Pfad zu erhalten (funktioniert auch mit PyInstaller)."""
    if getattr(sys, 'frozen', False):
        # Wenn in einem PyInstaller Bundle
        # sys._MEIPASS ist das temporäre Verzeichnis, wo PyInstaller die Dateien entpackt
        return sys._MEIPASS
    else:
        # Wenn normales Skript (aus dem src Ordner)
        # Gehe einen Ordner hoch, um den Projekt-Basisordner zu erhalten
        return os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def load_config():
    """Lädt die Konfiguration aus settings.ini."""
    config = configparser.ConfigParser()
    base_path = get_base_path()
    config_path = os.path.join(base_path, 'config', 'settings.ini') # settings.ini liegt im config-Unterordner vom Basis-Pfad

    if not os.path.exists(config_path):
        print(f"FEHLER: Konfigurationsdatei nicht gefunden unter {config_path}")
        # Gibt leere Konfiguration zurück oder beendet das Programm
        return configparser.ConfigParser() # Gibt ein leeres Config-Objekt zurück

    try:
        config.read(config_path, encoding='utf-8') # Versucht, die Datei zu lesen
        print(f"Konfiguration geladen von: {config_path}")
    except Exception as e:
         print(f"FEHLER beim Lesen der Konfiguration: {e}")

    return config

def load_master_codes(config):
    """
    Lädt die Masterliste der gültigen Codes aus einer Excel-Datei.

    Args:
        config (configparser.ConfigParser): Die geladene Anwendungskonfiguration.

    Returns:
        set: Ein Set mit allen gültigen Codes in Großbuchstaben,
             oder ein leeres Set im Fehlerfall oder wenn die Datei leer ist.
    """
    master_file_name = config.get('Files', 'master_codes_path', fallback='master_codes.xlsx')
    base_path = get_base_path()
    master_file_path = os.path.join(base_path, 'config', master_file_name) # Masterliste liegt im config-Unterordner

    valid_codes = set()
    expected_column_name = 'Code' # <-- ANPASSEN, falls Ihre Excel-Spalte anders heisst

    if not os.path.exists(master_file_path):
        # print(f"FEHLER: Mastercodes-Datei nicht gefunden unter {master_file_path}") # Wird in main.py besser behandelt
        return valid_codes # Gibt ein leeres Set zurück

    try:
        # Versucht, die Excel-Datei zu lesen
        df = pd.read_excel(master_file_path)

        if expected_column_name not in df.columns:
            print(f"FEHLER: Spalte '{expected_column_name}' nicht in Mastercodes-Datei '{master_file_name}' gefunden.")
            print(f"Verfügbare Spalten: {df.columns.tolist()}")
            return valid_codes # Gibt ein leeres Set zurück

        # Extrahiert die Codes aus der Spalte und fügt sie zum Set hinzu
        # .dropna(): Ignoriert leere Zellen in der Spalte
        # .astype(str): Stellt sicher, dass alle Einträge Strings sind
        # .str.strip(): Entfernt führende/abschließende Leerzeichen
        # .str.upper(): Konvertiert zu Großbuchstaben (wichtig für konsistenten Vergleich)
        valid_codes = set(df[expected_column_name].dropna().astype(str).str.strip().str.upper())

        print(f"Mastercodes-Datei '{master_file_name}' geladen ({len(valid_codes)} gültige Codes gefunden).")

    except FileNotFoundError:
         print(f"FEHLER: Mastercodes-Datei nicht gefunden: {master_file_path}")
         return set() # Gibt ein leeres Set zurück

    except Exception as e:
        print(f"FEHLER beim Lesen der Mastercodes-Datei '{master_file_name}': {e}")
        return set() # Gibt ein leeres Set zurück

    return valid_codes

# Beispiel der Nutzung (wird nicht ausgeführt, wenn importiert)
if __name__ == '__main__':
    # Für diesen Test muss eine dummy settings.ini und master_codes.xlsx im Ordner ../config existieren
    print("--- Test config.py ---")
    dummy_config = load_config()
    print(dummy_config.get('General', 'tesseract_path', fallback='Pfad nicht gefunden'))

    # Erstelle eine Dummy-Excel-Datei für den Test, falls nicht vorhanden
    dummy_master_path = os.path.join(get_base_path(), 'config', 'master_codes.xlsx')
    if not os.path.exists(dummy_master_path):
        print(f"Erstelle Dummy Mastercodes Datei: {dummy_master_path}")
        dummy_df = pd.DataFrame({'Code': ['A1X', 'B2Y', 'P0B', 'XYZ', 'a01x']})
        os.makedirs(os.path.dirname(dummy_master_path), exist_ok=True) # config Ordner erstellen
        dummy_df.to_excel(dummy_master_path, index=False)


    dummy_master_codes = load_master_codes(dummy_config)
    print(f"Geladene Dummy Master Codes: {dummy_master_codes}") # a01x sollte zu A01X werden, aber nicht bereinigt!
                                                                # Die Bereinigung passiert erst in core.py
                                                                # Set sollte {'A1X', 'B2Y', 'P0B', 'XYZ', 'A01X'} enthalten