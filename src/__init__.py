"""
PDF Code Comparator - Ein Tool zum Vergleich von Fahrzeugausstattungs-Codes

Dieses Package enthält alle Module für die OCR-basierte Extraktion und den 
intelligenten Vergleich von Codes zwischen Kaufverträgen und Auftragsbestätigungen.
"""

__version__ = "1.0.0"
__author__ = "PDF Code Comparator Team"

# Hauptmodule exportieren
from . import core
from . import config
from . import gui
from . import reporting
from . import ocr_correction
from . import code_filters

__all__ = [
    "core",
    "config", 
    "gui",
    "reporting",
    "ocr_correction",
    "code_filters"
]