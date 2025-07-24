# src/core.py
import fitz  # PyMuPDF
import re
import os
import time
from datetime import datetime
import subprocess
import tempfile
import io
from PIL import Image, ImageEnhance, ImageFilter
import cv2
import numpy as np
from .ocr_correction import OCRCorrector
from .code_filters import categorize_codes_by_type

# --- Erweiterte OCR-Korrektur Funktionen ---
def generate_all_ocr_variants(code):
    """
    Generiert alle möglichen OCR-Korrektur-Varianten eines Codes durch systematische Permutation.
    """
    # OCR-Verwechslungen (bidirektional)
    ocr_substitutions = {
        '0': ['O'],
        'O': ['0'],
        '8': ['B'],
        'B': ['8'],
        'I': ['1', 'L'],
        '1': ['I', 'L'],
        'L': ['I', '1'],
        '5': ['S'],
        'S': ['5'],
        '6': ['G'],
        'G': ['6'],
        '2': ['Z'],
        'Z': ['2']
    }
    
    def get_variants_for_position(char):
        """Gibt alle möglichen Varianten für ein Zeichen zurück (inklusive Original)"""
        variants = [char]  # Original immer dabei
        if char in ocr_substitutions:
            variants.extend(ocr_substitutions[char])
        return list(set(variants))  # Duplikate entfernen
    
    # Generiere alle Kombinationen
    import itertools
    
    position_variants = []
    for char in code:
        position_variants.append(get_variants_for_position(char))
    
    # Alle Permutationen generieren
    all_variants = []
    for combination in itertools.product(*position_variants):
        variant = ''.join(combination)
        if variant != code:  # Original nicht doppelt hinzufügen
            all_variants.append(variant)
    
    # Original an den Anfang, dann nach Anzahl Änderungen sortieren
    def count_changes(variant):
        return sum(1 for i, char in enumerate(variant) if i < len(code) and char != code[i])
    
    all_variants.sort(key=count_changes)
    return [code] + all_variants  # Original zuerst

def clean_code_advanced(code, master_codes_set=None):
    """
    Erweiterte Code-Bereinigung mit systematischer OCR-Korrektur.
    
    Ablauf:
    1. Grundbereinigung
    2. Systematische OCR-Korrektur (alle Permutationen)
    3. Falls nichts gefunden: 0/O an zweiter Stelle entfernen
    4. Nochmals systematische OCR-Korrektur
    """
    if not isinstance(code, str) or not code:
        return code.strip().upper() if isinstance(code, str) else ""

    # Grundbereinigung
    cleaned = code.strip()
    cleaned = re.sub(r'[.,:;)]+$', '', cleaned)
    cleaned = cleaned.upper()
    
    if not master_codes_set:
        return cleaned
    
    print(f"    Erweiterte Korrektur für: '{cleaned}'")
    
    # Phase 1: Systematische OCR-Korrektur
    variants = generate_all_ocr_variants(cleaned)
    
    for i, variant in enumerate(variants):
        if variant in master_codes_set:
            if variant != cleaned:
                print(f"      OCR-Korrektur: '{cleaned}' -> '{variant}' (Variante {i+1})")
            return variant
    
    # Phase 2: Falls 0 oder O an zweiter Stelle, entfernen und nochmals versuchen
    if len(cleaned) > 3 and len(cleaned) > 1 and cleaned[1] in ['0', 'O']:
        shortened = cleaned[0] + cleaned[2:]
        if len(shortened) >= 3:
            print(f"      Versuche ohne 2. Stelle: '{cleaned}' -> '{shortened}'")
            
            # Nochmals alle Varianten für die verkürzte Version
            shortened_variants = generate_all_ocr_variants(shortened)
            
            for i, variant in enumerate(shortened_variants):
                if variant in master_codes_set:
                    print(f"      0/O-Korrektur + OCR: '{cleaned}' -> '{variant}' (Verkürzt + Variante {i+1})")
                    return variant
    
    # Nichts gefunden, Original zurückgeben
    print(f"      Keine Korrektur gefunden für: '{cleaned}'")
    return cleaned

# --- Alte Funktion für Rückwärtskompatibilität ---
def clean_code(code, master_codes_set=None):
    """
    Wrapper für Rückwärtskompatibilität - verwendet die erweiterte Funktion.
    """
    return clean_code_advanced(code, master_codes_set)

def count_corrections_needed(original, corrected):
    """
    Zählt die Anzahl der Korrekturen zwischen Original und korrigiertem Code.
    """
    if original == corrected:
        return 0
    
    original = original.upper().strip()
    corrected = corrected.upper().strip()
    
    corrections = 0
    
    # Längenunterschiede (Entfernung/Hinzufügung von Zeichen)
    length_diff = abs(len(original) - len(corrected))
    corrections += length_diff
    
    # Zeichen-Substitutionen
    min_length = min(len(original), len(corrected))
    for i in range(min_length):
        if original[i] != corrected[i]:
            corrections += 1
    
    return corrections

def get_validated_context_codes(all_validated_codes, target_code, context_size=1):
    """
    Holt validierte Kontext-Codes vor und nach einem Ziel-Code.
    
    Args:
        all_validated_codes (list): Liste aller validierten Codes in Reihenfolge
        target_code (str): Der Ziel-Code
        context_size (int): Anzahl Codes vor und nach dem Ziel
    
    Returns:
        dict: {'before': [codes], 'after': [codes]}
    """
    try:
        index = all_validated_codes.index(target_code)
        before = all_validated_codes[max(0, index - context_size):index]
        after = all_validated_codes[index + 1:index + 1 + context_size]
        return {'before': before, 'after': after}
    except ValueError:
        return {'before': [], 'after': []}

def calculate_precise_probability(code, corrections_pdf1, corrections_pdf2, context_pdf1, context_pdf2, is_in_both=True):
    """
    Präzise Wahrscheinlichkeits-Berechnung nach den spezifischen Regeln:
    
    - Basis: 40% pro PDF wenn Code in Masterliste gefunden
    - -10% pro Korrektur die vorgenommen werden musste
    - Kontext-Bonus: 3 Codes vorher/nachher mit unterschiedlichen Gewichtungen
    
    Returns:
        tuple: (probability, context_details) - Wahrscheinlichkeit und Kontext-Details für Kommentare
    """
    probability = 0.0
    context_details = {'before_matches': 0, 'after_matches': 0, 'before_total': 0, 'after_total': 0}
    
    # Basis-Wahrscheinlichkeit: 40% pro PDF wenn Code in Masterliste
    if is_in_both:
        probability = 0.80  # 40% + 40% = 80% für beide PDFs
    else:
        probability = 0.40  # 40% für nur ein PDF
    
    # Korrektur-Abzüge
    total_corrections = corrections_pdf1 + corrections_pdf2
    probability -= total_corrections * 0.10  # -10% pro Korrektur
    
    # Stelle sicher, dass Wahrscheinlichkeit nicht unter 0 fällt
    probability = max(0.0, probability)
    
    if is_in_both:
        # Kontext-Bonus nur wenn Code in beiden PDFs gefunden
        context_bonus = 0.0
        
        # Bestimme Kontext-Gewichtungen basierend auf Korrekturen
        if total_corrections == 0:
            # Keine Korrekturen: Standard-Gewichtung
            before_weights = [0.10, 0.05, 0.02]  # 1., 2., 3. Code vorher
            after_weights = [0.08, 0.05, 0.02]   # 1., 2., 3. Code nachher
        elif total_corrections == 2 and corrections_pdf1 == 1 and corrections_pdf2 == 1:
            # Je eine Korrektur in beiden PDFs: Erhöhte Gewichtung
            before_weights = [0.10, 0.07, 0.03]  # 1., 2., 3. Code vorher
            after_weights = [0.10, 0.07, 0.03]   # 1., 2., 3. Code nachher
        else:
            # Andere Fälle: Standard-Gewichtung
            before_weights = [0.08, 0.05, 0.02]  # 1., 2., 3. Code vorher
            after_weights = [0.08, 0.05, 0.02]   # 1., 2., 3. Code nachher
        
        # Prüfe Kontext vorher (3 Codes)
        before_pdf1 = context_pdf1.get('before', [])
        before_pdf2 = context_pdf2.get('before', [])
        context_details['before_total'] = min(len(before_pdf1), len(before_pdf2), 3)
        
        for i in range(context_details['before_total']):
            if before_pdf1[-(i+1)] == before_pdf2[-(i+1)]:  # Von hinten nach vorne
                context_bonus += before_weights[i]
                context_details['before_matches'] += 1
        
        # Prüfe Kontext nachher (3 Codes)
        after_pdf1 = context_pdf1.get('after', [])
        after_pdf2 = context_pdf2.get('after', [])
        context_details['after_total'] = min(len(after_pdf1), len(after_pdf2), 3)
        
        for i in range(context_details['after_total']):
            if after_pdf1[i] == after_pdf2[i]:
                context_bonus += after_weights[i]
                context_details['after_matches'] += 1
        
        probability += context_bonus
    
    # Begrenze auf 0% - 100%
    probability = max(0.0, min(1.0, probability))
    
    return probability, context_details

def generate_korrekturmatch_comment(original, corrected, corrections_count, corrections_applied, context_details, pdf_source):
    """
    Generiert Kommentare speziell für Korrekturmatches nach den neuen Anforderungen.
    """
    # Korrekturmatch mit Anzahl Korrekturen
    comment_parts = [f"Korrekturmatch, {corrections_count} Korrekturen durchgeführt"]
    
    # Validierungs-Text für 3 Codes vor/nach
    validation_parts = []
    
    if context_details['before_matches'] > 0:
        if context_details['before_matches'] == 1:
            validation_parts.append("1 Code davor validiert")
        else:
            validation_parts.append(f"{context_details['before_matches']} Codes davor validiert")
    
    if context_details['after_matches'] > 0:
        if context_details['after_matches'] == 1:
            validation_parts.append("1 Code danach validiert")
        else:
            validation_parts.append(f"{context_details['after_matches']} Codes danach validiert")
    
    if validation_parts:
        comment_parts.extend(validation_parts)
    
    return ", ".join(comment_parts)

def generate_detailed_comment(original, corrected, corrections_pdf1, corrections_pdf2, context_details, pdf1_original=None, pdf2_original=None, corrections_applied=None):
    """
    Generiert detaillierte Kommentare mit PDF-spezifischen Korrektur-Informationen.
    """
    total_corrections = corrections_pdf1 + corrections_pdf2
    
    # Bestimme Match-Typ und Kontext-Größe
    if total_corrections == 0:
        match_type = "Direkter Match"
        corrections_text = None
        context_size = 1  # Bei direktem Match nur 1 Code vor/nach prüfen
    else:
        match_type = "Korrektur Match"
        context_size = 3  # Bei Korrekturen 3 Codes vor/nach prüfen
        
        # Verwende tatsächliche Korrektur-Details wenn verfügbar
        if corrections_applied:
            correction_parts = []
            
            if corrections_pdf1 > 0:
                pdf1_corrections = corrections_applied if pdf1_original else []
                if pdf1_corrections:
                    correction_parts.append(f"PDF1: {', '.join(pdf1_corrections)}")
            
            if corrections_pdf2 > 0:
                pdf2_corrections = corrections_applied if pdf2_original else []
                if pdf2_corrections:
                    correction_parts.append(f"PDF2: {', '.join(pdf2_corrections)}")
            
            # Fallback wenn keine PDF-spezifischen Details
            if not correction_parts and corrections_applied:
                correction_parts.append(', '.join(corrections_applied))
        else:
            # Fallback: Analysiere Unterschiede zwischen original und corrected
            correction_parts = []
            
            if corrections_pdf1 > 0 and pdf1_original:
                pdf1_details = analyze_corrections(pdf1_original, corrected)
                if pdf1_details:
                    correction_parts.append(f"PDF1: {pdf1_details}")
            
            if corrections_pdf2 > 0 and pdf2_original:
                pdf2_details = analyze_corrections(pdf2_original, corrected)
                if pdf2_details:
                    correction_parts.append(f"PDF2: {pdf2_details}")
            
            if not correction_parts and original != corrected:
                simple_details = analyze_corrections(original, corrected)
                if simple_details:
                    correction_parts.append(simple_details)
        
        if not correction_parts:
            correction_parts = ["OCR-Korrektur"]
        
        corrections_text = f"{total_corrections} Korrekturen ({', '.join(correction_parts)})"
    
    # Generiere Validierungs-Text basierend auf Kontext-Größe
    validation_parts = []
    
    if total_corrections == 0:
        # Direkter Match: nur 1 Code vor/nach
        if context_details['before_matches'] > 0:
            validation_parts.append("1 Code davor validiert")
        if context_details['after_matches'] > 0:
            validation_parts.append("1 Code danach validiert")
    else:
        # Korrekturen: bis zu 3 Codes vor/nach
        if context_details['before_matches'] > 0:
            if context_details['before_matches'] == 1:
                validation_parts.append("1 Code davor validiert")
            else:
                validation_parts.append(f"{context_details['before_matches']} Codes davor validiert")
        
        if context_details['after_matches'] > 0:
            if context_details['after_matches'] == 1:
                validation_parts.append("1 Code danach validiert")
            else:
                validation_parts.append(f"{context_details['after_matches']} Codes danach validiert")
    
    # Kombiniere alles
    if corrections_text:
        comment_parts = [match_type, corrections_text]
    else:
        comment_parts = [match_type]
    
    if validation_parts:
        comment_parts.extend(validation_parts)
    
    return ", ".join(comment_parts)

def analyze_corrections(original, corrected):
    """
    Analysiert welche spezifischen Korrekturen zwischen original und corrected durchgeführt wurden.
    """
    if original == corrected:
        return None
    
    correction_details = []
    
    # Prüfe auf 0/O-Entfernung an zweiter Stelle
    if len(original) > len(corrected) and len(original) > 1 and original[1] in ['0', 'O']:
        if original[0] + original[2:] == corrected:
            correction_details.append("0 an 2. Stelle entfernt")
            return ', '.join(correction_details)
    
    # Prüfe auf Zeichen-Substitutionen
    for i, (orig_char, corr_char) in enumerate(zip(original, corrected)):
        if orig_char != corr_char:
            if orig_char == '8' and corr_char == 'B':
                correction_details.append("8→B")
            elif orig_char == 'B' and corr_char == '8':
                correction_details.append("B→8")
            elif orig_char == 'I' and corr_char == '1':
                correction_details.append("I→1")
            elif orig_char == '1' and corr_char == 'I':
                correction_details.append("1→I")
            elif orig_char == '0' and corr_char == 'O':
                correction_details.append("0→O")
            elif orig_char == 'O' and corr_char == '0':
                correction_details.append("O→0")
            elif orig_char == '5' and corr_char == 'S':
                correction_details.append("5→S")
            elif orig_char == 'S' and corr_char == '5':
                correction_details.append("S→5")
            elif orig_char == '6' and corr_char == 'G':
                correction_details.append("6→G")
            elif orig_char == 'G' and corr_char == '6':
                correction_details.append("G→6")
            elif orig_char == '2' and corr_char == 'Z':
                correction_details.append("2→Z")
            elif orig_char == 'Z' and corr_char == '2':
                correction_details.append("Z→2")
    
    # Prüfe auf Leerzeichen-Entfernung
    if ' ' in original and ' ' not in corrected:
        correction_details.append("Leerzeichen entfernt")
    
    return ', '.join(correction_details) if correction_details else "OCR-Korrektur"

def calculate_unified_probability(original, corrected, context_pdf1, context_pdf2, master_codes_set):
    """
    Wrapper für Rückwärtskompatibilität - verwendet die neue präzise Berechnung.
    """
    corrections_count = count_corrections_needed(original, corrected)
    
    # Für diese Funktion nehmen wir an, dass es sich um einen Match in beiden PDFs handelt
    # und die Korrekturen gleichmäßig verteilt sind
    corrections_pdf1 = corrections_count // 2
    corrections_pdf2 = corrections_count - corrections_pdf1
    
    probability, context_details = calculate_precise_probability(
        corrected, corrections_pdf1, corrections_pdf2, 
        context_pdf1, context_pdf2, is_in_both=True
    )
    
    return probability

# --- Debug Funktion zum Speichern des OCR-Textes ---
def save_ocr_debug(pdf_base_name, page_num, text_lines):
    """Speichert die erkannten OCR-Textzeilen für eine Seite in einer Debug-Datei."""
    debug_dir = "debug_ocr_text"
    os.makedirs(debug_dir, exist_ok=True)
    safe_pdf_name = re.sub(r'[\\/*?:"<>|]', '', pdf_base_name)
    filename = f"{safe_pdf_name}_page_{page_num+1}_multi_ocr.txt"
    filepath = os.path.join(debug_dir, filename)

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"--- Multi-Ansatz OCR Text von {pdf_base_name}, Seite {page_num+1} ---\n\n")
            for line in text_lines:
                f.write(line + "\n")
            f.write("\n--------------------------------------------")
        # print(f"  OCR Debug Text gespeichert: {filepath}") # Optional: Bestätigung im Terminal
    except Exception as e:
        print(f"  FEHLER beim Speichern des OCR Debug Textes für Seite {page_num+1}: {e}")


# --- Extraktion und Vergleichslogik mit OCRmyPDF ---
def extract_codes(pdf_path, regex_pattern, tesseract_path, master_codes_set, return_raw_codes=False, is_pdf2=False):
    """
    Extrahiert Codes aus einer PDF-Datei mit OCRmyPDF und Tesseract.
    Wendet die clean_code Funktion an und validiert gegen die Masterliste.
    Erstellt Debug-Ausgaben für bessere Analyse.

    Args:
        pdf_path (str): Pfad zur PDF-Datei.
        regex_pattern (str): Das Regex-Muster zum Finden von Codes.
        tesseract_path (str): Pfad zur Tesseract-Executable.
        master_codes_set (set): Ein Set mit allen gültigen Codes aus der Masterliste.

    Returns:
        set: Ein Set mit den bereinigten und validierten, eindeutigen Codes aus der PDF.
             Gibt ein leeres Set zurück im Fehlerfall oder wenn keine Codes gefunden/validiert.
    """
    pdf_base_name = os.path.basename(pdf_path)
    print(f"Verarbeite PDF: {pdf_base_name} mit Multi-Ansatz OCR...")
    start_time = time.time()
    
    validated_codes_from_pdf = set()
    raw_codes_with_positions = []  # Für OCR-Korrektur: (code, page_num, position_in_page)
    
    try:
        # --- Erweiterte Tesseract OCR mit Bildverbesserung ---
        print("  Führe erweiterte OCR mit Tesseract durch...")
        
        doc = fitz.open(pdf_path)
        all_text_lines = []
        
        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)
            
            # Extrahiere nur linken Bereich (70% der Seitenbreite)
            page_width = page.rect.width
            page_height = page.rect.height
            left_area_rect = fitz.Rect(0, 0, page_width * 0.7, page_height)
            
            # Prüfe zuerst Text-Layer
            page_text = page.get_text(clip=left_area_rect)
            
            if len(page_text.strip()) < 50:  # Wenig Text = wahrscheinlich Scan
                print(f"    Seite {page_num + 1}: Führe Multi-Ansatz OCR durch...")
                
                # OPTIMIERT: Reduzierte DPI für bessere Performance
                pix = page.get_pixmap(clip=left_area_rect, dpi=300, alpha=False)  # Reduzierte DPI
                img_data = pix.tobytes("png")
                
                # Sammle OCR-Ergebnisse von verschiedenen Ansätzen
                all_ocr_results = []
                
                # --- ANSATZ 1: Standard Verbesserung ---
                img_pil = Image.open(io.BytesIO(img_data))
                enhancer = ImageEnhance.Contrast(img_pil)
                img_enhanced = enhancer.enhance(1.8)
                enhancer = ImageEnhance.Sharpness(img_enhanced)
                img_enhanced = enhancer.enhance(2.5)
                
                img_cv = cv2.cvtColor(np.array(img_enhanced), cv2.COLOR_RGB2BGR)
                gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
                
                # OPTIMIERT: Nur die besten 2 Binarisierungsmethoden
                methods = [
                    ("otsu", cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]),
                    ("denoised_otsu", cv2.threshold(cv2.fastNlMeansDenoising(gray), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1])
                ]
                
                # OPTIMIERT: Nur die besten 3 PSM-Modi
                psm_modes = ["3", "6", "8"]
                
                # Frühzeitige Beendigung wenn genug Codes gefunden
                codes_found = 0
                target_codes = 10  # Beende wenn 10+ Codes gefunden
                
                for method_name, processed_img in methods:
                    if codes_found >= target_codes:
                        break
                        
                    for psm in psm_modes:
                        if codes_found >= target_codes:
                            break
                            
                        temp_img_path = f"temp_{method_name}_psm{psm}_page_{page_num}.png"
                        cv2.imwrite(temp_img_path, processed_img)
                        
                        try:
                            # OPTIMIERT: Nur eine Tesseract-Konfiguration
                            cmd = [tesseract_path, temp_img_path, "stdout", "-l", "deu+eng+fra+ita", "--psm", psm, 
                                   "-c", "tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"]
                            
                            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', timeout=10)
                            
                            if result.returncode == 0:
                                ocr_text = result.stdout.strip()
                                if ocr_text:
                                    lines = [line.strip() for line in ocr_text.splitlines() if line.strip()]
                                    all_ocr_results.append({
                                        'method': f"{method_name}_psm{psm}",
                                        'text': ocr_text,
                                        'lines': lines
                                    })
                                    # Zähle potenzielle Codes für frühzeitige Beendigung
                                    codes_found += len([line for line in lines if re.search(r'[A-Z0-9]{3,7}', line)])
                        
                        except Exception as e:
                            pass  # Ignoriere Fehler einzelner Versuche
                        
                        finally:
                            if os.path.exists(temp_img_path):
                                os.remove(temp_img_path)
                
                # --- ANSATZ 2: OPTIMIERT - Nur bei Bedarf skalieren ---
                # Nur wenn noch nicht genug Codes gefunden wurden
                if codes_found < target_codes:
                    # Nur eine Skalierung testen
                    scale_factor = 2.0
                    try:
                        # Skaliere Bild
                        img_scaled = img_pil.resize((int(img_pil.width * scale_factor), int(img_pil.height * scale_factor)), Image.LANCZOS)
                        
                        # Verarbeitung
                        img_cv = cv2.cvtColor(np.array(img_scaled), cv2.COLOR_RGB2BGR)
                        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
                        processed = cv2.threshold(cv2.fastNlMeansDenoising(gray), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
                        
                        temp_img_path = f"temp_scaled_{scale_factor}_page_{page_num}.png"
                        cv2.imwrite(temp_img_path, processed)
                        
                        cmd = [tesseract_path, temp_img_path, "stdout", "-l", "deu+eng+fra+ita", "--psm", "6", 
                               "-c", "tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"]
                        
                        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', timeout=10)
                        
                        if result.returncode == 0:
                            ocr_text = result.stdout.strip()
                            if ocr_text:
                                lines = [line.strip() for line in ocr_text.splitlines() if line.strip()]
                                all_ocr_results.append({
                                    'method': f"scaled_{scale_factor}",
                                    'text': ocr_text,
                                    'lines': lines
                                })
                                codes_found += len([line for line in lines if re.search(r'[A-Z0-9]{3,7}', line)])
                    
                    except Exception:
                        pass
                    
                    finally:
                        if os.path.exists(temp_img_path):
                            os.remove(temp_img_path)
                
                # --- Kombiniere alle Ergebnisse ---
                all_text_from_ocr = set()
                for result in all_ocr_results:
                    for line in result['lines']:
                        all_text_from_ocr.add(line)
                
                page_lines = list(all_text_from_ocr)
                print(f"    Seite {page_num + 1}: {len(page_lines)} einzigartige Zeilen aus {len(all_ocr_results)} OCR-Versuchen")
                
                # Debug: Speichere alle OCR-Versuche
                debug_all_results = []
                for result in all_ocr_results:
                    debug_all_results.append(f"=== {result['method']} ===")
                    debug_all_results.extend(result['lines'])
                    debug_all_results.append("")
                
                save_ocr_debug(pdf_base_name, page_num, debug_all_results)
                
            else:
                print(f"    Seite {page_num + 1}: Nutze Text-Layer ({len(page_text.strip())} Zeichen)")
                page_lines = [line.strip() for line in page_text.splitlines() if line.strip()]
                
                # Debug: Speichere Text-Layer
                save_ocr_debug(pdf_base_name, page_num, ["=== TEXT-LAYER ==="] + page_lines)
            
            # Sammle alle Textzeilen
            all_text_lines.extend(page_lines)
        
        doc.close()
        
        # --- Codes mit Regex finden und Positionen merken ---
        raw_codes = []
        
        # Einfachere Logik: Durchlaufe alle Textzeilen
        page_line_counter = 0  # Separate Zeilenzählung für Seitenschätzung
        for i, line in enumerate(all_text_lines):
            found_codes = re.findall(r'\b' + regex_pattern + r'\b', line.upper())
            for j, code in enumerate(found_codes):
                raw_codes.append(code)
                # Schätze Seite basierend auf Zeilennummer
                if is_pdf2:
                    # PDF2: Separate Seitenzählung (beginnt bei 1, unabhängig von PDF1)
                    estimated_page = (page_line_counter // 50) + 1
                else:
                    # PDF1: Normale Seitenzählung
                    estimated_page = (i // 50) + 1
                raw_codes_with_positions.append((code, estimated_page, i * 10 + j))
            
            if found_codes:  # Nur Zeilen mit Codes zählen für PDF2
                page_line_counter += 1
        
        # --- DEBUGGING: Gefundene Roh-Codes ausgeben ---
        print(f"  Gefundene Roh-Codes ({len(raw_codes)}): {raw_codes}")
        
        # Keine speziellen Filter für PDF2 mehr nötig (Minus Options Anforderung entfernt)

        # --- Codes bereinigen und validieren (mit detaillierter Korrektur-Dokumentation) ---
        correction_info = []  # Sammle Korrektur-Informationen für Reporting
        
        for i, code in enumerate(raw_codes):
            original_code = code.upper().strip()
            
            # SCHRITT 1: Prüfe direkten Match mit Masterliste (nach Grundbereinigung)
            basic_cleaned = re.sub(r'[.,:;)]+$', '', original_code.strip()).upper()
            
            if basic_cleaned in master_codes_set:
                # DIREKTER MATCH - keine Korrekturen nötig
                validated_codes_from_pdf.add(basic_cleaned)
                print(f"  Direkter Match: '{original_code}' -> '{basic_cleaned}' (keine Korrekturen)")
                continue
            
            # SCHRITT 2: Code ist nicht direkt in Masterliste - versuche Korrekturen
            print(f"  '{original_code}' nicht in Masterliste - versuche Korrekturen...")
            
            # Dokumentiere alle durchgeführten Korrekturen
            corrections_applied = []
            current_code = basic_cleaned
            
            # Phase 1: Systematische OCR-Korrektur (alle Permutationen)
            variants = generate_all_ocr_variants(current_code)
            found_match = None
            
            for i_var, variant in enumerate(variants):
                if variant in master_codes_set:
                    found_match = variant
                    if variant != current_code:
                        # Dokumentiere welche Korrekturen gemacht wurden
                        variant_corrections = analyze_corrections(current_code, variant)
                        if variant_corrections:
                            corrections_applied.append(variant_corrections)
                        print(f"    OCR-Korrektur: '{current_code}' -> '{variant}' (Variante {i_var+1})")
                    break
            
            # Phase 2: Falls 0 oder O an zweiter Stelle, entfernen und nochmals versuchen
            if not found_match and len(current_code) > 3 and len(current_code) > 1 and current_code[1] in ['0', 'O']:
                shortened = current_code[0] + current_code[2:]
                if len(shortened) >= 3:
                    corrections_applied.append("0 an 2. Stelle entfernt")
                    print(f"    0/O-Entfernung: '{current_code}' -> '{shortened}'")
                    current_code = shortened
                    
                    # Nochmals alle Varianten für die verkürzte Version
                    shortened_variants = generate_all_ocr_variants(current_code)
                    
                    for i_var, variant in enumerate(shortened_variants):
                        if variant in master_codes_set:
                            found_match = variant
                            if variant != current_code:
                                # Dokumentiere zusätzliche Korrekturen
                                additional_corrections = analyze_corrections(current_code, variant)
                                if additional_corrections:
                                    corrections_applied.append(additional_corrections)
                                print(f"    Zusätzliche OCR-Korrektur: '{current_code}' -> '{variant}' (Variante {i_var+1})")
                            break
            
            # Ergebnis verarbeiten
            if found_match:
                validated_codes_from_pdf.add(found_match)
                
                # Dokumentiere alle Korrekturen
                if corrections_applied:
                    estimated_page = (i // 10) + 1 if i < len(raw_codes_with_positions) else 1
                    
                    correction_info.append({
                        'original': original_code,
                        'corrected': found_match,
                        'page': estimated_page,
                        'position': i,
                        'method': 'Erweiterte OCR-Korrektur',
                        'corrections_applied': corrections_applied,
                        'corrections_count': len(corrections_applied)
                    })
                    print(f"  Korrektur-Match dokumentiert: '{original_code}' -> '{found_match}' ({len(corrections_applied)} Korrekturen: {', '.join(corrections_applied)})")
                else:
                    print(f"  Unerwarteter Fall: Match gefunden aber keine Korrekturen dokumentiert")
            else:
                # Nichts gefunden, auch nicht mit Korrekturen
                print(f"  Code '{original_code}' konnte nicht korrigiert werden (nicht in Masterliste)")
        
        print(f"  Validierte Codes gefunden: {len(validated_codes_from_pdf)}")
        end_time = time.time()
        print(f"  Verarbeitung abgeschlossen in {end_time - start_time:.2f} Sekunden.")
        
        if return_raw_codes:
            return validated_codes_from_pdf, raw_codes_with_positions, all_text_lines, correction_info
        else:
            return validated_codes_from_pdf

    except subprocess.CalledProcessError as e:
        print(f"FEHLER: Tesseract Aufruf fehlgeschlagen: {e}")
        print("Stellen Sie sicher, dass Tesseract korrekt installiert ist.")
        if return_raw_codes:
            return set(), [], []
        else:
            return set()
    except FileNotFoundError:
        print(f"FEHLER: PDF-Datei nicht gefunden: {pdf_path}")
        if return_raw_codes:
            return set(), [], []
        else:
            return set()
    except Exception as e:
        print(f"FEHLER bei der Verarbeitung von {pdf_base_name}: {e}")
        if return_raw_codes:
            return set(), [], []
        else:
            return set()

# Erweiterte compare_codes Funktion mit bidirektionaler OCR-Korrektur
def compare_codes_with_correction(codes_pdf1, codes_pdf2, raw_codes_pdf1, raw_codes_pdf2, master_codes_set, all_text_lines_pdf1=None, correction_info_pdf1=None, correction_info_pdf2=None):
    """
    Vergleicht zwei Sets von Codes und versucht erweiterte OCR-Korrekturen mit Kontext-Analyse.
    Implementiert spezielle Behandlung für Steuer-Codes (I-Codes).
    """
    print("Vergleiche Codes mit erweiterter bidirektionaler OCR-Korrektur...")
    
    # --- NEUE ANFORDERUNG 3: Kategorisiere Codes nach Typ ---
    pdf1_categories = categorize_codes_by_type(codes_pdf1)
    pdf2_categories = categorize_codes_by_type(codes_pdf2)
    
    print(f"  PDF1: {len(pdf1_categories['normal'])} normale, {len(pdf1_categories['control'])} Steuer-Codes")
    print(f"  PDF2: {len(pdf2_categories['normal'])} normale, {len(pdf2_categories['control'])} Steuer-Codes")
    
    # Basis-Vergleich für normale Codes
    normal_in_both = pdf1_categories['normal'].intersection(pdf2_categories['normal'])
    normal_only_in_pdf1 = pdf1_categories['normal'].difference(pdf2_categories['normal'])
    normal_only_in_pdf2 = pdf2_categories['normal'].difference(pdf1_categories['normal'])
    
    # Basis-Vergleich für Steuer-Codes (I-Codes)
    control_in_both = pdf1_categories['control'].intersection(pdf2_categories['control'])
    control_only_in_pdf1 = pdf1_categories['control'].difference(pdf2_categories['control'])
    control_only_in_pdf2 = pdf2_categories['control'].difference(pdf1_categories['control'])
    
    # Kombiniere für Gesamtvergleich
    in_both = normal_in_both.union(control_in_both)
    only_in_pdf1 = normal_only_in_pdf1.union(control_only_in_pdf1)
    only_in_pdf2 = normal_only_in_pdf2.union(control_only_in_pdf2)
    
    print(f"Vor Korrektur: Beide={len(in_both)}, Nur PDF1={len(only_in_pdf1)}, Nur PDF2={len(only_in_pdf2)}")
    
    # OCR-Korrektur anwenden
    corrector = OCRCorrector(master_codes_set)
    
    # Verwende raw_codes_pdf2 direkt (keine Minus Options Filterung mehr nötig)
    filtered_raw_codes_pdf2 = raw_codes_pdf2
    
    # Erstelle sortierte Listen für Kontext-Analyse (nur validierte Codes)
    pdf1_codes_list = [code for code, page, pos in sorted(raw_codes_pdf1, key=lambda x: (x[1], x[2])) if clean_code_advanced(code, master_codes_set) in master_codes_set]
    pdf2_codes_list = [code for code, page, pos in sorted(filtered_raw_codes_pdf2, key=lambda x: (x[1], x[2])) if clean_code_advanced(code, master_codes_set) in master_codes_set]
    
    # Alle Korrekturen sammeln (inklusive erweiterte OCR-Korrekturen)
    all_corrections = []
    corrected_codes_pdf1 = set(codes_pdf1)
    
    # Erstelle Liste aller validierten Codes für Kontext-Analyse
    all_validated_pdf1 = [clean_code_advanced(code, master_codes_set) for code, page, pos in sorted(raw_codes_pdf1, key=lambda x: (x[1], x[2]))]
    all_validated_pdf1 = [code for code in all_validated_pdf1 if code in master_codes_set]
    
    all_validated_pdf2 = [clean_code_advanced(code, master_codes_set) for code, page, pos in sorted(filtered_raw_codes_pdf2, key=lambda x: (x[1], x[2]))]
    all_validated_pdf2 = [code for code in all_validated_pdf2 if code in master_codes_set]
    
    print(f"  Validierte Code-Sequenzen: PDF1={len(all_validated_pdf1)}, PDF2={len(all_validated_pdf2)}")
    
    # Füge erweiterte OCR-Korrekturen aus extract_codes hinzu
    if correction_info_pdf1:
        for corr_info in correction_info_pdf1:
            # Hole Kontext für diese Korrektur
            context_pdf1 = get_validated_context_codes(all_validated_pdf1, corr_info['corrected'], context_size=3)
            context_pdf2 = get_validated_context_codes(all_validated_pdf2, corr_info['corrected'], context_size=3)
            
            # Berechne präzise Wahrscheinlichkeit für erweiterte OCR-Korrekturen
            corrections_count = count_corrections_needed(corr_info['original'], corr_info['corrected'])
            
            # Für erweiterte OCR-Korrekturen: Alle Korrekturen sind in PDF1
            # WICHTIG: 3 Codes vor/nach prüfen da Korrekturen durchgeführt wurden
            probability, context_details = calculate_precise_probability(
                corr_info['corrected'], 
                corrections_count, 0,  # Alle Korrekturen in PDF1, 0 in PDF2
                context_pdf1, context_pdf2, 
                is_in_both=True  # Code wird in beiden PDFs gefunden (nach Korrektur)
            )
            
            # Generiere Korrekturmatch-Kommentar mit 3 Codes vor/nach
            corrections_details = corr_info.get('corrections_applied', [])
            detailed_comment = generate_korrekturmatch_comment(
                corr_info['original'], corr_info['corrected'], 
                corrections_count, corrections_details, context_details, "PDF1"
            )
            
            all_corrections.append({
                'original': corr_info['original'],
                'corrected': corr_info['corrected'],
                'page': corr_info['page'],
                'probability': probability,
                'method': detailed_comment,
                'factors': ['Erweiterte OCR-Korrektur', 'Kontext-Validierung', 'Master-Code gefunden'],
                'correction_type': 'Erweiterte OCR-Korrektur'
            })
            # WICHTIG: Füge korrigierten Code zu corrected_codes_pdf1 hinzu
            corrected_codes_pdf1.add(corr_info['corrected'])
            print(f"  Erweiterte OCR-Korrektur hinzugefügt: '{corr_info['original']}' -> '{corr_info['corrected']}' (P={probability:.0%})")
    
    if correction_info_pdf2:
        for corr_info in correction_info_pdf2:
            context_pdf1 = get_validated_context_codes(all_validated_pdf1, corr_info['corrected'], context_size=3)
            context_pdf2 = get_validated_context_codes(all_validated_pdf2, corr_info['corrected'], context_size=3)
            
            corrections_count = count_corrections_needed(corr_info['original'], corr_info['corrected'])
            
            # Für PDF2 erweiterte OCR-Korrekturen: Alle Korrekturen sind in PDF2
            probability, context_details = calculate_precise_probability(
                corr_info['corrected'], 
                0, corrections_count,  # 0 in PDF1, alle Korrekturen in PDF2
                context_pdf1, context_pdf2, 
                is_in_both=True  # Code wird in beiden PDFs gefunden (nach Korrektur)
            )
            
            # Generiere detaillierten Kommentar
            # Generiere Korrekturmatch-Kommentar für PDF2
            corrections_details = corr_info.get('corrections_applied', [])
            detailed_comment = generate_korrekturmatch_comment(
                corr_info['original'], corr_info['corrected'], 
                corrections_count, corrections_details, context_details, "PDF2"
            )
            
            all_corrections.append({
                'original': corr_info['original'],
                'corrected': corr_info['corrected'],
                'page': f"PDF2 Seite {corr_info['page']}",
                'probability': probability,
                'method': detailed_comment,
                'factors': ['Erweiterte OCR-Korrektur', 'Kontext-Validierung', 'Master-Code gefunden'],
                'correction_type': 'Erweiterte OCR-Korrektur'
            })
            # Für PDF2 Korrekturen: Diese sind bereits in codes_pdf2, keine Änderung nötig
            print(f"  Erweiterte OCR-Korrektur PDF2 hinzugefügt: '{corr_info['original']}' -> '{corr_info['corrected']}' (P={probability:.0%})")
    
    # 1. Intelligente Leerzeichen-Korrekturen (nur relevante Kombinationen)
    print("  Suche intelligente Leerzeichen-getrennte Codes...")
    
    whitespace_combinations = []
    
    if all_text_lines_pdf1:
        # Sammle alle einzelnen Tokens die potenzielle Code-Fragmente sein könnten
        potential_fragments = set()
        for line in all_text_lines_pdf1:
            tokens = line.split()
            for token in tokens:
                clean_token = corrector.clean_whitespace(token).upper()
                # Nur Tokens die wie Code-Fragmente aussehen (1-4 Zeichen, alphanumerisch)
                if 1 <= len(clean_token) <= 4 and clean_token.isalnum():
                    potential_fragments.add(clean_token)
        
        print(f"    Gefundene potenzielle Code-Fragmente: {len(potential_fragments)}")
        
        # Prüfe nur Kombinationen die zu bekannten Codes führen könnten
        for line_idx, line in enumerate(all_text_lines_pdf1):
            tokens = line.split()
            
            # Prüfe nur 2-3 Token Kombinationen (nicht 4-5)
            for start_idx in range(len(tokens)):
                for end_idx in range(start_idx + 2, min(start_idx + 4, len(tokens) + 1)):
                    token_group = tokens[start_idx:end_idx]
                    
                    # Basis-Kombination
                    base_combined = corrector.clean_whitespace(''.join(token_group))
                    
                    # Nur prüfen wenn die Länge stimmt und es potenzielle Fragmente enthält
                    if 3 <= len(base_combined) <= 7:
                        # Prüfe ob mindestens ein Fragment in bekannten Codes vorkommt
                        is_relevant = False
                        for token in token_group:
                            clean_token = corrector.clean_whitespace(token).upper()
                            if any(clean_token in master_code for master_code in master_codes_set):
                                is_relevant = True
                                break
                        
                        if is_relevant:
                            whitespace_combinations.append({
                                'combined': base_combined,
                                'parts': token_group,
                                'line': line_idx,
                                'method': 'Leerzeichen entfernt',
                                'substitutions': [],
                                'penalty': 0
                            })
                            
                            # Nur eine einfache Substitution pro relevante Kombination
                            simple_variants = corrector.generate_simple_variants(base_combined)
                            for variant in simple_variants[:3]:  # Maximal 3 Varianten
                                if variant != base_combined and 3 <= len(variant) <= 7:
                                    whitespace_combinations.append({
                                        'combined': variant,
                                        'parts': token_group,
                                        'line': line_idx,
                                        'method': f'Leerzeichen entfernt + einfache Substitution',
                                        'substitutions': ['OCR-Korrektur'],
                                        'penalty': 0.1
                                    })
        
        print(f"    Generierte Leerzeichen-Kombinationen: {len(whitespace_combinations)}")
    else:
        # Fallback: Einfache Kombinationen
        raw_codes_only = [code for code, page, pos in raw_codes_pdf1]
        for i in range(len(raw_codes_only) - 1):
            combined = corrector.clean_whitespace(raw_codes_only[i] + raw_codes_only[i + 1])
            if 3 <= len(combined) <= 7:
                whitespace_combinations.append({
                    'combined': combined,
                    'parts': [raw_codes_only[i], raw_codes_only[i + 1]],
                    'line': i,
                    'method': 'Leerzeichen entfernt',
                    'substitutions': [],
                    'penalty': 0
                })
    
    for combo in whitespace_combinations:
        combined_cleaned = clean_code_advanced(combo['combined'], master_codes_set)
        if combined_cleaned in master_codes_set and combined_cleaned in codes_pdf2:
            # Verbesserte Kontext-Analyse mit nur validierten Codes
            try:
                context_pdf1 = corrector.get_validated_context_codes(raw_codes_pdf1, master_codes_set, combo['line'])
                context_pdf2 = corrector.get_validated_context_codes(filtered_raw_codes_pdf2, master_codes_set, 
                                                                    pdf2_codes_list.index(combined_cleaned) if combined_cleaned in pdf2_codes_list else 0)
            except:
                context_pdf1 = {'before': [], 'after': []}
                context_pdf2 = {'before': [], 'after': []}
            
            # Höhere Wahrscheinlichkeit für komplexere Korrekturen
            has_substitutions = len(combo['substitutions']) > 0
            correction_type = "whitespace_and_substitution" if has_substitutions else "whitespace_removal"
            
            # Verwende präzise Wahrscheinlichkeits-Berechnung für Leerzeichen-Korrekturen
            context_pdf1_unified = get_validated_context_codes(all_validated_pdf1, combined_cleaned, context_size=3)
            context_pdf2_unified = get_validated_context_codes(all_validated_pdf2, combined_cleaned, context_size=3)
            
            corrections_count = count_corrections_needed(" ".join(combo['parts']), combined_cleaned)
            
            # Leerzeichen-Korrekturen sind normalerweise nur in PDF1
            probability, context_details = calculate_precise_probability(
                combined_cleaned, 
                corrections_count, 0,  # Alle Korrekturen in PDF1
                context_pdf1_unified, context_pdf2_unified, 
                is_in_both=True  # Code wird in beiden PDFs gefunden
            )
            
            # Generiere detaillierten Kommentar für Leerzeichen-Korrektur
            # Generiere Korrekturmatch-Kommentar für Leerzeichen-Korrektur
            detailed_comment = generate_korrekturmatch_comment(
                " ".join(combo['parts']), combined_cleaned, 
                corrections_count, ["Leerzeichen entfernt"], context_details, "PDF1"
            )
            
            factors = []  # Keine Faktoren mehr nötig
            
            # Anpassung für komplexe Korrekturen
            if has_substitutions:
                # Bonus für erfolgreiche komplexe Korrektur, aber Penalty für mehrfache Substitutionen
                penalty = combo.get('penalty', 0)
                probability += 0.1 - penalty  # Extra Bonus minus Penalty
                probability = max(0.1, min(1.0, probability))
            
            if probability >= 0.6:
                corrected_codes_pdf1.add(combined_cleaned)
                all_corrections.append({
                    'original': " ".join(combo['parts']),
                    'corrected': combined_cleaned,
                    'page': f"Zeile {combo['line'] + 1}",
                    'probability': probability,
                    'method': detailed_comment,
                    'factors': factors,
                    'correction_type': 'Korrekturmatch'
                })
                print(f"  Erweiterte Korrektur: '{' '.join(combo['parts'])}' -> '{combined_cleaned}' ({combo['method']}, P={probability:.0%})")
    
    # 2. Substitutions-Korrekturen (bidirektional)
    print("  Suche OCR-Verwechslungen...")
    for target_code in only_in_pdf2:
        # Generiere mögliche Fehlerkennungen
        possible_variants = corrector.generate_variants(target_code)
        
        # Prüfe rohe Codes aus PDF1
        for raw_code, page_num, position in raw_codes_pdf1:
            cleaned_raw = clean_code_advanced(raw_code, master_codes_set)
            
            if cleaned_raw in possible_variants and cleaned_raw not in master_codes_set:
                # Kontext-Analyse
                try:
                    pdf1_pos = pdf1_codes_list.index(cleaned_raw) if cleaned_raw in pdf1_codes_list else position
                    pdf2_pos = pdf2_codes_list.index(target_code) if target_code in pdf2_codes_list else 0
                except ValueError:
                    pdf1_pos = position
                    pdf2_pos = 0
                
                context_pdf1 = corrector.get_context_codes(pdf1_codes_list, pdf1_pos)
                context_pdf2 = corrector.get_context_codes(pdf2_codes_list, pdf2_pos)
                
                # Bestimme Korrektur-Typ
                has_substitution = any(char1 in corrector.substitutions and char2 in corrector.substitutions[char1] 
                                     for char1, char2 in zip(cleaned_raw, target_code) if char1 != char2)
                correction_type = "substitution" if has_substitution else "other"
                
                # Verwende präzise Wahrscheinlichkeits-Berechnung für OCR-Verwechslungen
                context_pdf1_unified = get_validated_context_codes(all_validated_pdf1, target_code, context_size=3)
                context_pdf2_unified = get_validated_context_codes(all_validated_pdf2, target_code, context_size=3)
                
                corrections_count = count_corrections_needed(cleaned_raw, target_code)
                
                # OCR-Verwechslungen sind normalerweise nur in PDF1
                probability, context_details = calculate_precise_probability(
                    target_code, 
                    corrections_count, 0,  # Alle Korrekturen in PDF1
                    context_pdf1_unified, context_pdf2_unified, 
                    is_in_both=True  # Code wird in beiden PDFs gefunden
                )
                
                # Generiere detaillierten Kommentar für OCR-Verwechslung
                # Generiere Korrekturmatch-Kommentar für OCR-Verwechslung
                correction_detail = analyze_corrections(cleaned_raw, target_code)
                detailed_comment = generate_korrekturmatch_comment(
                    cleaned_raw, target_code, 
                    corrections_count, [correction_detail], context_details, "PDF1"
                )
                
                factors = []  # Keine Faktoren mehr nötig
                
                if probability >= 0.6:
                    corrected_codes_pdf1.add(target_code)
                    all_corrections.append({
                        'original': cleaned_raw,
                        'corrected': target_code,
                        'page': page_num,
                        'probability': probability,
                        'method': detailed_comment,
                        'factors': factors,
                        'correction_type': 'Korrekturmatch'
                    })
                    print(f"  OCR-Korrektur: '{cleaned_raw}' -> '{target_code}' (Seite {page_num}, P={probability:.0%})")
    
    # 3. Klassifiziere Matches korrekt (Direkter Match vs. Korrekturmatch)
    print("  Klassifiziere Matches basierend auf tatsächlich durchgeführten Korrekturen...")
    
    # Sammle alle Codes die Korrekturen benötigten
    codes_with_corrections = set()
    for corr_info in (correction_info_pdf1 or []) + (correction_info_pdf2 or []):
        if corr_info.get('corrections_count', 0) > 0:
            codes_with_corrections.add(corr_info['corrected'])
    
    for code in in_both:
        try:
            # Prüfe ob dieser Code Korrekturen benötigte
            had_corrections = code in codes_with_corrections
            
            if had_corrections:
                # Bereits als Korrekturmatch in correction_info dokumentiert
                print(f"    Code '{code}' bereits als Korrekturmatch dokumentiert")
                continue
            else:
                # ECHTER direkter Match - keine Korrekturen waren nötig
                context_pdf1_unified = get_validated_context_codes(all_validated_pdf1, code, context_size=1)
                context_pdf2_unified = get_validated_context_codes(all_validated_pdf2, code, context_size=1)
                
                # Präzise Wahrscheinlichkeits-Berechnung für echte direkte Matches
                probability, context_details = calculate_precise_probability(
                    code, 0, 0,  # 0 Korrekturen in beiden PDFs
                    context_pdf1_unified, context_pdf2_unified, is_in_both=True
                )
                
                # Generiere Kommentar für echten direkten Match (nur 1 Code vor/nach)
                detailed_comment = generate_detailed_comment(code, code, 0, 0, context_details, None, None, None)
                
                all_corrections.append({
                    'original': code,
                    'corrected': code,
                    'page': 'Beide',
                    'probability': probability,
                    'method': detailed_comment,
                    'factors': [],
                    'correction_type': 'Direkter Match'
                })
                
                print(f"    Echter direkter Match: '{code}' (P={probability:.0%}) - keine Korrekturen nötig")
            
        except ValueError:
            # Code nicht in sortierter Liste gefunden
            pass
    
    # Neuer Vergleich nach Korrekturen mit Kategorisierung
    corrected_pdf1_categories = categorize_codes_by_type(corrected_codes_pdf1)
    corrected_pdf2_categories = categorize_codes_by_type(codes_pdf2)
    
    # Normale Codes nach Korrektur
    normal_in_both_corrected = corrected_pdf1_categories['normal'].intersection(corrected_pdf2_categories['normal'])
    normal_only_in_pdf1_corrected = corrected_pdf1_categories['normal'].difference(corrected_pdf2_categories['normal'])
    normal_only_in_pdf2_corrected = corrected_pdf2_categories['normal'].difference(corrected_pdf1_categories['normal'])
    
    # Steuer-Codes nach Korrektur
    control_in_both_corrected = corrected_pdf1_categories['control'].intersection(corrected_pdf2_categories['control'])
    control_only_in_pdf1_corrected = corrected_pdf1_categories['control'].difference(corrected_pdf2_categories['control'])
    control_only_in_pdf2_corrected = corrected_pdf2_categories['control'].difference(corrected_pdf1_categories['control'])
    
    # Kombinierte Ergebnisse
    in_both_corrected = normal_in_both_corrected.union(control_in_both_corrected)
    only_in_pdf1_corrected = normal_only_in_pdf1_corrected.union(control_only_in_pdf1_corrected)
    only_in_pdf2_corrected = normal_only_in_pdf2_corrected.union(control_only_in_pdf2_corrected)
    
    print(f"Nach Korrektur: Beide={len(in_both_corrected)}, Nur PDF1={len(only_in_pdf1_corrected)}, Nur PDF2={len(only_in_pdf2_corrected)}")
    print(f"  Normale Codes: Beide={len(normal_in_both_corrected)}, Nur PDF1={len(normal_only_in_pdf1_corrected)}, Nur PDF2={len(normal_only_in_pdf2_corrected)}")
    print(f"  Steuer-Codes: Beide={len(control_in_both_corrected)}, Nur PDF1={len(control_only_in_pdf1_corrected)}, Nur PDF2={len(control_only_in_pdf2_corrected)}")
    print(f"Korrekturen durchgeführt: {len([c for c in all_corrections if c['correction_type'] != 'Direkter Match'])}")
    
    return {
        'original': {
            'in_both': in_both,
            'only_in_pdf1': only_in_pdf1,
            'only_in_pdf2': only_in_pdf2,
            # Kategorisierte Original-Ergebnisse
            'normal': {
                'in_both': normal_in_both,
                'only_in_pdf1': normal_only_in_pdf1,
                'only_in_pdf2': normal_only_in_pdf2
            },
            'control': {
                'in_both': control_in_both,
                'only_in_pdf1': control_only_in_pdf1,
                'only_in_pdf2': control_only_in_pdf2
            }
        },
        'corrected': {
            'in_both': in_both_corrected,
            'only_in_pdf1': only_in_pdf1_corrected,
            'only_in_pdf2': only_in_pdf2_corrected,
            # Kategorisierte korrigierte Ergebnisse
            'normal': {
                'in_both': normal_in_both_corrected,
                'only_in_pdf1': normal_only_in_pdf1_corrected,
                'only_in_pdf2': normal_only_in_pdf2_corrected
            },
            'control': {
                'in_both': control_in_both_corrected,
                'only_in_pdf1': control_only_in_pdf1_corrected,
                'only_in_pdf2': control_only_in_pdf2_corrected
            }
        },
        'corrections': all_corrections,
        'legend': corrector.probability_legend
    }

# Alte Funktion für Rückwärtskompatibilität
def compare_codes(codes_pdf1, codes_pdf2):
    """
    Vergleicht zwei Sets von Codes und bildet die drei Mengen.
    """
    print("Vergleiche Codes...")
    in_both = codes_pdf1.intersection(codes_pdf2)
    only_in_pdf1 = codes_pdf1.difference(codes_pdf2)
    only_in_pdf2 = codes_pdf2.difference(codes_pdf1)

    print(f"Ergebnis: Beide={len(in_both)}, Nur PDF1={len(only_in_pdf1)}, Nur PDF2={len(only_in_pdf2)}")

    return in_both, only_in_pdf1, only_in_pdf2