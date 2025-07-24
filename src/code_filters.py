# src/code_filters.py
"""
Neue Filterfunktionen für spezielle Code-Behandlung
"""
import re

def is_control_code(code):
    """
    Prüft ob ein Code ein Steuer-Code ist (beginnt mit 'I' oder 'i').
    
    Args:
        code (str): Der zu prüfende Code
        
    Returns:
        bool: True wenn es ein Steuer-Code ist
    """
    if not isinstance(code, str) or not code:
        return False
    return code.upper().startswith('I')

# Minus Options Funktionen entfernt - nicht mehr benötigt

def categorize_codes_by_type(codes_set):
    """
    Kategorisiert Codes nach Typ (Normal vs. Steuer-Codes).
    
    Args:
        codes_set (set): Set von Codes
        
    Returns:
        dict: {'normal': set, 'control': set}
    """
    normal_codes = set()
    control_codes = set()
    
    for code in codes_set:
        if is_control_code(code):
            control_codes.add(code)
        else:
            normal_codes.add(code)
    
    return {
        'normal': normal_codes,
        'control': control_codes
    }