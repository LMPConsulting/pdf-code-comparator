# src/main.py
import tkinter as tk
from tkinter import messagebox
import os
import sys
import threading
import time # Für Zeitmessung der Initialisierung

# Relative Importe (werden im Thread geladen, um GUI-Start zu beschleunigen)
from . import config
from . import gui
# from . import core # Importiert im Thread
# from . import reporting # Importiert im Thread

master_codes_set = set()
app_config = None
# OCRmyPDF wird direkt in core.py verwendet

def start_comparison_process(pdf1_path, pdf2_path, app_gui):
    """
    Startet den eigentlichen Vergleichsprozess in einem separaten Thread.
    Greift auf globale Variablen master_codes_set, app_config, easyocr_reader zu.
    """
    # Prüfen, ob Konfiguration und Mastercodes geladen wurden
    if not app_config or not master_codes_set:
        app_gui.update_status("FEHLER: Anwendung nicht korrekt initialisiert.")
        messagebox.showerror("FEHLER", "Anwendung nicht korrekt initialisiert (Konfiguration/Mastercodes fehlen).")
        app_gui.enable_start_button()
        return

    app_gui.update_status("Verarbeitung gestartet...")

    # Laden von core und reporting erst im Thread, um die GUI-Initialisierung nicht zu verzögern
    # und Abhängigkeiten besser zu handhaben (besonders für PyInstaller --onefile)
    try:
        from . import core
        from . import reporting
    except ImportError as e:
        print(f"FEHLER: Konnte interne Module (core/reporting) nicht importieren: {e}")
        app_gui.update_status("FEHLER: Internes Modul fehlt.")
        messagebox.showerror("FEHLER", f"Internes Modul fehlt: {e}")
        app_gui.enable_start_button()
        return


    output_dir = os.path.dirname(pdf1_path)
    report_format = app_config.get('Report', 'format', fallback='xlsx')
    regex_pattern = app_config.get('Codes', 'regex_pattern', fallback=r"[A-Z0-9]{3,7}")
    # Tesseract Pfad für OCRmyPDF
    tesseract_path = app_config.get('General', 'tesseract_path', fallback='')
    tesseract_is_available = (tesseract_path and os.path.exists(tesseract_path))


    def run_in_thread():
        """Funktion, die im separaten Thread läuft."""
        try:
            app_gui.update_status(f"Verarbeite PDF 1 mit Multi-OCR ({os.path.basename(pdf1_path)})...")
            # Multi-OCR Extraktion mit rohen Codes für Korrektur
            result_pdf1 = core.extract_codes(pdf1_path, regex_pattern, tesseract_path, master_codes_set, return_raw_codes=True)
            if result_pdf1 is None or (isinstance(result_pdf1, tuple) and result_pdf1[0] is None): # Fehlerbehandlung aus core.extract_codes
                app_gui.update_status(f"FEHLER bei Verarbeitung von PDF 1. Siehe Terminal/Log.")
                messagebox.showerror("Verarbeitungsfehler", f"Fehler bei der Verarbeitung von {os.path.basename(pdf1_path)}. Details in der Konsole.")
                return # Thread beenden

            app_gui.update_status(f"Verarbeite PDF 2 mit Multi-OCR ({os.path.basename(pdf2_path)})...")
            # Multi-OCR Extraktion mit rohen Codes für Korrektur
            codes_pdf1, raw_codes_pdf1, all_text_lines_pdf1, correction_info_pdf1 = result_pdf1
            
            result_pdf2 = core.extract_codes(pdf2_path, regex_pattern, tesseract_path, master_codes_set, return_raw_codes=True, is_pdf2=True)
            if result_pdf2 is None or (isinstance(result_pdf2, tuple) and result_pdf2[0] is None): # Fehlerbehandlung aus core.extract_codes
                 app_gui.update_status(f"FEHLER bei Verarbeitung von PDF 2. Siehe Terminal/Log.")
                 messagebox.showerror("Verarbeitungsfehler", f"Fehler bei der Verarbeitung von {os.path.basename(pdf2_path)}. Details in der Konsole.")
                 return # Thread beenden
            
            codes_pdf2, raw_codes_pdf2, all_text_lines_pdf2, correction_info_pdf2 = result_pdf2

            app_gui.update_status("Vergleiche Codes mit intelligenter OCR-Korrektur...")
            comparison_result = core.compare_codes_with_correction(codes_pdf1, codes_pdf2, raw_codes_pdf1, raw_codes_pdf2, master_codes_set, all_text_lines_pdf1, correction_info_pdf1, correction_info_pdf2)
            
            # Extrahiere Ergebnisse
            in_both = comparison_result['corrected']['in_both']
            only_in_pdf1 = comparison_result['corrected']['only_in_pdf1'] 
            only_in_pdf2 = comparison_result['corrected']['only_in_pdf2']
            corrections = comparison_result['corrections']

            if in_both or only_in_pdf1 or only_in_pdf2 or corrections:
                report_path = reporting.generate_enhanced_report(
                    comparison_result['original'], comparison_result['corrected'], 
                    comparison_result['corrections'], output_dir, report_format,
                    raw_codes_pdf1, raw_codes_pdf2
                )
            else:
                 report_path = None # Kein Report, wenn absolut keine Codes gefunden/validiert wurden


            # --- Ergebnisnachricht (FR-05, IO-03) ---
            # Abweichungen gefunden, wenn Codes NUR in PDF1 oder NUR in PDF2 sind
            diff_found = len(only_in_pdf1) > 0 or len(only_in_pdf2) > 0

            if diff_found:
                result_message = "VERGLEICH ABGESCHLOSSEN: Abweichungen gefunden!"
                detail_message = f"Details im Report: {report_path}" if report_path else "Report konnte nicht erstellt werden."
                app_gui.update_status(result_message)
                messagebox.showwarning("Ergebnis: Abweichungen", f"{result_message}\n{detail_message}")
            else:
                # Keine Abweichungen, aber prüfen ob überhaupt Codes gefunden wurden
                if len(in_both) > 0:
                    result_message = "VERGLEICH ABGESCHLOSSEN: Keine Abweichungen gefunden (Codes in beiden Dokumenten stimmen überein)."
                else:
                    result_message = "VERGLEICH ABGESCHLOSSEN: Keine Codes gefunden oder keine relevanten Codes in der Masterliste."

                detail_message = f"Report erstellt: {report_path}" if report_path else "Kein Report erstellt (keine Codes gefunden/validiert)."
                app_gui.update_status(result_message)
                messagebox.showinfo("Ergebnis: Keine Abweichungen", f"{result_message}\n{detail_message}")


        except Exception as e:
            error_message = f"Ein unerwarteter Fehler ist aufgetreten: {e}"
            print(error_message) # Auch im Terminal ausgeben
            app_gui.update_status(error_message)
            messagebox.showerror("Unerwarteter Fehler", error_message)
        finally:
            # Wichtig: Button nach Abschluss (egal ob Erfolg oder Fehler) wieder aktivieren
            app_gui.master.after(100, app_gui.enable_start_button) # Nutzt after(), um im GUI-Thread zu laufen


    # Startet die Funktion run_in_thread in einem separaten Thread
    thread = threading.Thread(target=run_in_thread)
    thread.start()


if __name__ == "__main__":
    # 1. Konfiguration laden (global speichern)
    app_config = config.load_config()

    if not app_config or not app_config.sections():
         messagebox.showerror("FEHLER", "Konfiguration (settings.ini) konnte nicht geladen werden oder ist leer.")
         sys.exit("Konfiguration fehlt.")

    # 2. Master Codes Liste laden (global speichern)
    master_codes_set = config.load_master_codes(app_config)

    if not master_codes_set:
         messagebox.showwarning("WARNUNG", "Master Codes Liste (master_codes.xlsx) konnte nicht geladen werden oder ist leer.\n"
                                        "Der Vergleich wird keine gültigen Codes finden!")
         # WARNUNG statt FEHLER, da die App starten soll, aber die Validierung nicht funktioniert


    # 3. Tesseract Pfad prüfen (wichtig für OCRmyPDF)
    tesseract_path_check = app_config.get('General', 'tesseract_path', fallback='')
    if not tesseract_path_check or not os.path.exists(tesseract_path_check):
         messagebox.showwarning("Konfigurations-Warnung",
                                f"Tesseract-Pfad '{tesseract_path_check}' ist ungültig oder nicht gesetzt.\n"
                                "Die OCR-Verarbeitung mit OCRmyPDF wird fehlschlagen.")
    else:
        print(f"Tesseract gefunden: {tesseract_path_check}")
        # Setze Tesseract-Pfad in PATH für OCRmyPDF
        tesseract_dir = os.path.dirname(tesseract_path_check)
        os.environ['PATH'] = tesseract_dir + os.pathsep + os.environ.get('PATH', '')
        print("Tesseract-Pfad wurde temporär zum System-PATH hinzugefügt.")


    # 4. GUI erstellen
    root = tk.Tk()
    # Übergeben Sie die Funktion, die beim Button-Klick aufgerufen werden soll.
    # Die Funktion start_comparison_process greift jetzt direkt auf die globalen
    # master_codes_set, app_config und easyocr_reader zu.
    app = gui.AppGUI(root,
                     start_comparison_callback=lambda p1, p2: start_comparison_process(p1, p2, app))


    # 5. GUI starten
    root.mainloop()