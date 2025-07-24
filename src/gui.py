# src/gui.py
import tkinter as tk
from tkinter import filedialog, messagebox, ttk # ttk für modernere Widgets
import os

class AppGUI:
    def __init__(self, master, start_comparison_callback=None):
        """
        Initialisiert die GUI.

        Args:
            master (tk.Tk): Das Haupt-Tkinter-Fenster.
            start_comparison_callback (function): Die Funktion, die aufgerufen
                                                 werden soll, wenn der 'Vergleich starten'-Button
                                                 geklickt wird. Diese Funktion sollte
                                                 zwei Dateipfade als Argumente erwarten.
        """
        self.master = master
        master.title("PDF Code Comparator")
        master.geometry("500x300") # Fenstergröße anpassen
        master.resizable(False, False) # Fenstergröße nicht änderbar machen

        self.start_comparison_callback = start_comparison_callback

        # Styling für modernere Elemente
        style = ttk.Style()
        style.theme_use("clam") # Oder "alt", "default", "classic"

        # Frame für die Dateiauswahl
        file_frame = ttk.LabelFrame(master, text="PDF Dateien auswählen", padding="10")
        file_frame.pack(pady=10, padx=10, fill="x")

        # --- PDF 1 Auswahl ---
        self.label_pdf1 = ttk.Label(file_frame, text="PDF 1 (Kaufvertrag):")
        self.label_pdf1.grid(row=0, column=0, sticky="w", padx=5, pady=5)

        self.entry_pdf1 = ttk.Entry(file_frame, width=40)
        self.entry_pdf1.grid(row=0, column=1, padx=5, pady=5)

        self.button_pdf1 = ttk.Button(file_frame, text="Durchsuchen", command=self.select_pdf1)
        self.button_pdf1.grid(row=0, column=2, padx=5, pady=5)

        # --- PDF 2 Auswahl ---
        self.label_pdf2 = ttk.Label(file_frame, text="PDF 2 (AB):")
        self.label_pdf2.grid(row=1, column=0, sticky="w", padx=5, pady=5)

        self.entry_pdf2 = ttk.Entry(file_frame, width=40)
        self.entry_pdf2.grid(row=1, column=1, padx=5, pady=5)

        self.button_pdf2 = ttk.Button(file_frame, text="Durchsuchen", command=self.select_pdf2)
        self.button_pdf2.grid(row=1, column=2, padx=5, pady=5)

        # Frame für Button und Status
        action_frame = ttk.Frame(master, padding="10")
        action_frame.pack(pady=5, padx=10, fill="x")

        # --- Vergleich starten Button ---
        self.button_start = ttk.Button(action_frame, text="Vergleich starten", command=self.on_start_button_click)
        self.button_start.pack(pady=5)

        # --- Status / Ergebnis Anzeige ---
        self.status_label = ttk.Label(master, text="Bereit.", anchor="center") # anchor="center" für Zentrierung
        self.status_label.pack(pady=10, fill="x")


    def select_pdf1(self):
        """Öffnet Dateidialog zur Auswahl von PDF 1."""
        filepath = filedialog.askopenfilename(
            initialdir=".", # Startverzeichnis ('.': aktueller Ordner)
            title="PDF 1 (Kaufvertrag) auswählen",
            filetypes=(("PDF files", "*.pdf"), ("All files", "*.*"))
        )
        if filepath:
            self.entry_pdf1.delete(0, tk.END) # Löscht alten Inhalt
            self.entry_pdf1.insert(0, filepath) # Fügt neuen Pfad ein
            self.update_status("PDF 1 ausgewählt.")

    def select_pdf2(self):
        """Öffnet Dateidialog zur Auswahl von PDF 2."""
        filepath = filedialog.askopenfilename(
            initialdir=".",
            title="PDF 2 (Auftragsbestätigung) auswählen",
            filetypes=(("PDF files", "*.pdf"), ("All files", "*.*"))
        )
        if filepath:
            self.entry_pdf2.delete(0, tk.END)
            self.entry_pdf2.insert(0, filepath)
            self.update_status("PDF 2 ausgewählt.")

    def on_start_button_click(self):
        """Wird aufgerufen, wenn der Start-Button geklickt wird."""
        pdf1_path = self.entry_pdf1.get()
        pdf2_path = self.entry_pdf2.get()

        if not pdf1_path or not pdf2_path:
            messagebox.showwarning("Eingabefehler", "Bitte beide PDF-Dateien auswählen!")
            return

        if self.start_comparison_callback:
            # Deaktiviert den Button, um Mehrfachklicks zu verhindern
            self.button_start.config(state=tk.DISABLED)
            # Führt den Callback aus (verbunden in main.py)
            self.start_comparison_callback(pdf1_path, pdf2_path)
            # Button wird nach Abschluss des Callbacks in main.py wieder aktiviert

    def update_status(self, message):
        """Aktualisiert den Text im Status-Label."""
        self.status_label.config(text=message)
        self.master.update_idletasks() # Sorgt dafür, dass die GUI sofort aktualisiert wird

    def enable_start_button(self):
         """Aktiviert den Start-Button wieder."""
         self.button_start.config(state=tk.NORMAL)

# Beispielaufruf (wird nicht ausgeführt, wenn importiert)
if __name__ == '__main__':
    root = tk.Tk()
    # Wenn gui.py direkt gestartet wird, gibt es keinen Callback, daher None
    app = AppGUI(root, start_comparison_callback=None)
    root.mainloop()