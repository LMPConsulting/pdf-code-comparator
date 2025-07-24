# src/ocr_correction.py
import re
from itertools import product
from difflib import SequenceMatcher

class OCRCorrector:
    """
    Intelligente OCR-Korrektur basierend auf bekannten Verwechslungsgefahren
    und Masterliste-Abgleich mit Wahrscheinlichkeitsberechnung.
    """
    
    def __init__(self, master_codes_set):
        self.master_codes_set = master_codes_set
        
        # Erweiterte bidirektionale OCR-Verwechslungen
        self.substitutions = {
            'B': ['8'],           # B ↔ 8
            '8': ['B'],           
            'O': ['0'],           # O ↔ 0
            '0': ['O'],           
            'I': ['1', 'l'],      # I ↔ 1 ↔ l (kleines L)
            '1': ['I', 'l'],      
            'l': ['I', '1'],      
            'S': ['5', 'Z'],      # S ↔ 5 ↔ Z (alle drei können verwechselt werden)
            '5': ['S', 'Z'],      
            'Z': ['S', '5', '2'], # Z ↔ S ↔ 5 ↔ 2
            '2': ['Z'],           
            'G': ['6'],           # G ↔ 6
            '6': ['G'],           
            'E': ['F'],           # E ↔ F (für ElW ↔ FlW)
            'F': ['E'],           
        }
        
        # Wahrscheinlichkeitslegende entsprechend der spezifizierten Logik
        self.probability_legend = {
            "PDF_Code_ohne_Korrektur": "40% - PDF Code in Master-Liste ohne Korrektur",
            "PDF_Code_mit_Korrektur": "30% - PDF Code in Master-Liste mit Korrektur",
            "Beide_PDFs_ohne_Korrektur": "80% - Selber Code ist auf beiden PDFs in Master-Liste ohne Korrektur (40% + 40%)",
            "Beide_PDFs_mit_Korrektur": "70% - Selber Code ist auf beiden PDFs in Master-Liste mit Korrektur (30% + 40% oder 40% + 30%)",
            "Direkt_davor_gleich": "10% - Direkt davor gleicher Code in beiden PDFs (oder 20% wenn erster/letzter Code)",
            "Direkt_danach_gleich": "10% - Direkt danach gleicher Code in beiden PDFs (oder 20% wenn erster/letzter Code)",
            "1_Code_davor_gleich": "7% - Bei Korrektur: 1. Code davor gleich in beiden PDFs",
            "2_Code_davor_gleich": "2% - Bei Korrektur: 2. Code davor gleich in beiden PDFs", 
            "3_Code_davor_gleich": "1% - Bei Korrektur: 3. Code davor gleich in beiden PDFs",
            "1_Code_danach_gleich": "7% - Bei Korrektur: 1. Code danach gleich in beiden PDFs",
            "2_Code_danach_gleich": "2% - Bei Korrektur: 2. Code danach gleich in beiden PDFs",
            "3_Code_danach_gleich": "1% - Bei Korrektur: 3. Code danach gleich in beiden PDFs",
            "Erster_letzter_Bonus": "20% - Bonus für ersten/letzten Code wenn nur eine Richtung prüfbar"
        }
        
        self.corrections_made = []  # Dokumentation aller Korrekturen
    
    def clean_whitespace(self, code):
        """Entfernt Leerzeichen und andere Whitespace-Zeichen."""
        return re.sub(r'\s+', '', code.strip())
    
    def apply_zero_rule(self, code):
        """Wendet die spezielle 0-Regel an."""
        if len(code) > 3 and len(code) > 1 and code[1] == '0':
            potential_cleaned = code[0] + code[2:]
            if len(potential_cleaned) >= 3:
                return potential_cleaned
        return code
    
    def generate_simple_variants(self, code):
        """
        Generiert nur einfache Varianten eines Codes (maximal 1-2 Substitutionen).
        Optimiert für Performance bei Leerzeichen-Korrekturen.
        """
        variants = []
        
        # Originaler Code (nach Whitespace-Bereinigung)
        cleaned_code = self.clean_whitespace(code).upper()
        
        # Nur einzelne Substitutionen (nicht alle Kombinationen)
        for i, char in enumerate(cleaned_code):
            if char in self.substitutions:
                for replacement in self.substitutions[char]:
                    variant = list(cleaned_code)
                    variant[i] = replacement
                    variant_code = ''.join(variant)
                    
                    # Teste auch mit 0-Regel
                    variant_with_zero_rule = self.apply_zero_rule(variant_code)
                    
                    if variant_code not in variants:
                        variants.append(variant_code)
                    if variant_with_zero_rule not in variants and variant_with_zero_rule != variant_code:
                        variants.append(variant_with_zero_rule)
        
        return variants
    
    def generate_variants(self, code):
        """
        Generiert alle möglichen Varianten eines Codes basierend auf 
        bekannten OCR-Verwechslungen.
        """
        variants = set()
        
        # Originaler Code (nach Whitespace-Bereinigung)
        cleaned_code = self.clean_whitespace(code).upper()
        variants.add(cleaned_code)
        
        # Generiere Varianten durch Zeichensubstitution
        positions_to_substitute = []
        for i, char in enumerate(cleaned_code):
            if char in self.substitutions:
                positions_to_substitute.append((i, char, self.substitutions[char]))
        
        # Generiere alle Kombinationen von Substitutionen
        if positions_to_substitute:
            # Erstelle alle möglichen Kombinationen
            substitution_combinations = []
            for pos, original_char, replacements in positions_to_substitute:
                substitution_combinations.append([(pos, original_char)] + [(pos, repl) for repl in replacements])
            
            # Generiere Kartesisches Produkt aller Kombinationen
            for combination in product(*substitution_combinations):
                variant = list(cleaned_code)
                substitutions_made = []
                
                for pos, new_char in combination:
                    if variant[pos] != new_char:
                        substitutions_made.append((pos, variant[pos], new_char))
                        variant[pos] = new_char
                
                variant_code = ''.join(variant)
                
                # Teste auch mit 0-Regel
                variant_with_zero_rule = self.apply_zero_rule(variant_code)
                
                variants.add(variant_code)
                variants.add(variant_with_zero_rule)
        
        return variants
    
    def find_advanced_whitespace_combinations(self, all_text_lines):
        """
        DEPRECATED: Diese Funktion wurde durch die intelligente Leerzeichen-Korrektur 
        in core.py ersetzt. Wird nur noch für Rückwärtskompatibilität beibehalten.
        """
        print("  WARNUNG: find_advanced_whitespace_combinations ist deprecated und wird übersprungen")
        return []
    
    def generate_substitution_variants(self, text):
        """
        Generiert einfache Substitutions-Varianten eines Textes.
        Optimiert für Performance - maximal 2 Substitutionen.
        """
        variants = []
        
        # Nur einzelne Substitutionen für bessere Performance
        for i, char in enumerate(text):
            if char in self.substitutions:
                for replacement in self.substitutions[char]:
                    variant = list(text)
                    variant[i] = replacement
                    variant_text = ''.join(variant)
                    substitutions_text = f"{char}→{replacement}"
                    variants.append((variant_text, substitutions_text, 0))
        
        # Maximal eine doppelte Substitution für häufige Fälle
        if len(text) <= 5:  # Nur bei kurzen Codes
            for i in range(len(text)):
                for j in range(i + 1, len(text)):
                    char1, char2 = text[i], text[j]
                    if char1 in self.substitutions and char2 in self.substitutions:
                        for repl1 in self.substitutions[char1][:1]:  # Nur erste Substitution
                            for repl2 in self.substitutions[char2][:1]:  # Nur erste Substitution
                                variant = list(text)
                                variant[i] = repl1
                                variant[j] = repl2
                                variant_text = ''.join(variant)
                                substitutions_text = f"{char1}→{repl1}, {char2}→{repl2}"
                                variants.append((variant_text, substitutions_text, 0.2))  # Höhere Penalty
        
        return variants[:10]  # Maximal 10 Varianten
    
    def filter_codes_before_minus_options(self, all_text_lines, raw_codes_with_positions):
        """
        Filtert Codes heraus, die nach "Minus Options" Text gefunden wurden.
        """
        minus_options_found = False
        minus_options_line = -1
        
        # Suche nach "Minus Options" Text
        for line_idx, line in enumerate(all_text_lines):
            if "minus options" in line.lower() or "minus-options" in line.lower():
                minus_options_found = True
                minus_options_line = line_idx
                print(f"  'Minus Options' gefunden in Zeile {line_idx + 1} - ignoriere nachfolgende Codes")
                break
        
        if not minus_options_found:
            return raw_codes_with_positions
        
        # Filtere Codes die nach "Minus Options" kommen
        filtered_codes = []
        for code, page, position in raw_codes_with_positions:
            # Schätze Zeile basierend auf Position (grob)
            estimated_line = position // 10  # Annahme: ~10 Codes pro Zeile
            
            if estimated_line <= minus_options_line:
                filtered_codes.append((code, page, position))
            else:
                print(f"  Code '{code}' ignoriert (nach Minus Options)")
        
        return filtered_codes
    
    def get_context_codes(self, codes_list, position, context_size=3):
        """
        Holt Kontext-Codes um eine bestimmte Position in einer Code-Liste.
        """
        context = {
            'before': [],
            'after': []
        }
        
        if 0 <= position < len(codes_list):
            # Codes davor
            start_before = max(0, position - context_size)
            context['before'] = codes_list[start_before:position]
            
            # Codes danach
            end_after = min(len(codes_list), position + context_size + 1)
            context['after'] = codes_list[position + 1:end_after]
        
        return context
    
    def get_validated_context_codes(self, all_codes_with_positions, master_codes_set, position, context_size=3):
        """
        Holt nur validierte Codes als Kontext (ignoriert Seitenumbrüche und ungültige Codes).
        """
        # Filtere nur validierte Codes
        validated_codes = []
        for code, page, pos in all_codes_with_positions:
            cleaned = self.clean_whitespace(code).upper()
            if len(cleaned) > 3 and cleaned[1] == '0':
                potential_cleaned = cleaned[0] + cleaned[2:]
                if len(potential_cleaned) >= 3:
                    cleaned = potential_cleaned
            
            if cleaned in master_codes_set:
                validated_codes.append((cleaned, page, pos))
        
        # Sortiere nach Position
        validated_codes.sort(key=lambda x: (x[1], x[2]))  # Nach Seite, dann Position
        
        # Finde die Position des aktuellen Codes
        current_index = -1
        for i, (code, page, pos) in enumerate(validated_codes):
            if pos == position:
                current_index = i
                break
        
        context = {
            'before': [],
            'after': []
        }
        
        if current_index >= 0:
            # Codes davor (nur validierte)
            for i in range(max(0, current_index - context_size), current_index):
                context['before'].append(validated_codes[i][0])
            
            # Codes danach (nur validierte)
            for i in range(current_index + 1, min(len(validated_codes), current_index + context_size + 1)):
                context['after'].append(validated_codes[i][0])
        
        return context
    
    def calculate_enhanced_probability(self, original_code, corrected_code, context_pdf1, context_pdf2, 
                                     in_pdf2, has_correction, correction_type):
        """
        Wahrscheinlichkeitsberechnung basierend auf der spezifizierten Logik:
        - PDF1 Code in Master-Liste: 40% (ohne Korrektur) oder 30% (mit Korrektur)
        - PDF2 Code in Master-Liste: 40% (ohne Korrektur) oder 30% (mit Korrektur)
        - Kontext-Analyse mit unterschiedlichen Gewichtungen
        """
        probability = 0.0
        factors_applied = []
        
        # Bestimme ob PDF1 eine Korrektur benötigte
        pdf1_needs_correction = (correction_type != "direct_match")
        
        # PDF1 Basis-Wahrscheinlichkeit
        if pdf1_needs_correction:
            probability += 0.3  # 30% für Korrektur
            factors_applied.append("PDF_Code_mit_Korrektur")
        else:
            probability += 0.4  # 40% ohne Korrektur
            factors_applied.append("PDF_Code_ohne_Korrektur")
        
        # PDF2 Basis-Wahrscheinlichkeit (wenn Code auch in PDF2 gefunden)
        if in_pdf2:
            probability += 0.4  # 40% - PDF2 Code direkt gefunden
            if pdf1_needs_correction:
                factors_applied.append("Beide_PDFs_mit_Korrektur")
            else:
                factors_applied.append("Beide_PDFs_ohne_Korrektur")
        
        # Kontext-Analyse
        if not pdf1_needs_correction and in_pdf2:
            # Direkter Match in beiden PDFs: Prüfe direkte Nachbarn (10% jeweils)
            # Spezialfall: Erster/letzter Code bekommt 20% wenn nur eine Richtung prüfbar
            
            is_first_code = len(context_pdf1['before']) == 0 or len(context_pdf2['before']) == 0
            is_last_code = len(context_pdf1['after']) == 0 or len(context_pdf2['after']) == 0
            
            if is_first_code and not is_last_code:
                # Erster Code: Nur danach prüfen, dafür 20%
                if (context_pdf1['after'] and context_pdf2['after'] and 
                    len(context_pdf1['after']) > 0 and len(context_pdf2['after']) > 0 and
                    context_pdf1['after'][0] == context_pdf2['after'][0]):
                    probability += 0.2
                    factors_applied.append("Erster_letzter_Bonus")
            elif is_last_code and not is_first_code:
                # Letzter Code: Nur davor prüfen, dafür 20%
                if (context_pdf1['before'] and context_pdf2['before'] and 
                    len(context_pdf1['before']) > 0 and len(context_pdf2['before']) > 0 and
                    context_pdf1['before'][-1] == context_pdf2['before'][-1]):
                    probability += 0.2
                    factors_applied.append("Erster_letzter_Bonus")
            else:
                # Normaler Fall: Beide Richtungen prüfen (10% jeweils)
                if (context_pdf1['before'] and context_pdf2['before'] and 
                    len(context_pdf1['before']) > 0 and len(context_pdf2['before']) > 0 and
                    context_pdf1['before'][-1] == context_pdf2['before'][-1]):
                    probability += 0.1
                    factors_applied.append("Direkt_davor_gleich")
                
                if (context_pdf1['after'] and context_pdf2['after'] and 
                    len(context_pdf1['after']) > 0 and len(context_pdf2['after']) > 0 and
                    context_pdf1['after'][0] == context_pdf2['after'][0]):
                    probability += 0.1
                    factors_applied.append("Direkt_danach_gleich")
        
        elif pdf1_needs_correction:
            # Bei Korrektur: Erweiterte Kontext-Prüfung (3 Codes davor/danach)
            # Maximal 20% durch Kontext (10% davor + 10% danach)
            
            # Codes davor prüfen: 7% + 2% + 1% = 10%
            for i in range(min(3, len(context_pdf1['before']), len(context_pdf2['before']))):
                if context_pdf1['before'][-(i+1)] == context_pdf2['before'][-(i+1)]:
                    if i == 0:  # 1. Code davor
                        probability += 0.07
                        factors_applied.append("1_Code_davor_gleich")
                    elif i == 1:  # 2. Code davor
                        probability += 0.02
                        factors_applied.append("2_Code_davor_gleich")
                    elif i == 2:  # 3. Code davor
                        probability += 0.01
                        factors_applied.append("3_Code_davor_gleich")
            
            # Codes danach prüfen: 7% + 2% + 1% = 10%
            for i in range(min(3, len(context_pdf1['after']), len(context_pdf2['after']))):
                if context_pdf1['after'][i] == context_pdf2['after'][i]:
                    if i == 0:  # 1. Code danach
                        probability += 0.07
                        factors_applied.append("1_Code_danach_gleich")
                    elif i == 1:  # 2. Code danach
                        probability += 0.02
                        factors_applied.append("2_Code_danach_gleich")
                    elif i == 2:  # 3. Code danach
                        probability += 0.01
                        factors_applied.append("3_Code_danach_gleich")
            
            # Wenn Code auch in PDF2 gefunden: zusätzliche 5% für direkten Kontext
            if in_pdf2:
                if (context_pdf1['before'] and context_pdf2['before'] and 
                    len(context_pdf1['before']) > 0 and len(context_pdf2['before']) > 0 and
                    context_pdf1['before'][-1] == context_pdf2['before'][-1]):
                    probability += 0.05
                    factors_applied.append("Direkt_davor_gleich")
                
                if (context_pdf1['after'] and context_pdf2['after'] and 
                    len(context_pdf1['after']) > 0 and len(context_pdf2['after']) > 0 and
                    context_pdf1['after'][0] == context_pdf2['after'][0]):
                    probability += 0.05
                    factors_applied.append("Direkt_danach_gleich")
        
        # Begrenze auf Maximum 100%
        probability = min(1.0, probability)
        
        return round(probability, 2), factors_applied
    
    def document_correction(self, original_code, corrected_code, page_num, method, probability):
        """Dokumentiert eine durchgeführte Korrektur."""
        self.corrections_made.append({
            'original_code': original_code,
            'corrected_code': corrected_code,
            'page': page_num,
            'method': method,
            'probability': probability,
            'substitutions': self.get_substitutions_made(original_code, corrected_code)
        })
    
    def get_substitutions_made(self, original, corrected):
        """Ermittelt welche Zeichen-Substitutionen gemacht wurden."""
        substitutions = []
        
        # Whitespace-Entfernung
        orig_clean = self.clean_whitespace(original)
        if orig_clean != original:
            substitutions.append(f"Leerzeichen entfernt: '{original}' -> '{orig_clean}'")
        
        # Zeichen-Substitutionen
        for i, (char1, char2) in enumerate(zip(orig_clean, corrected)):
            if char1 != char2:
                substitutions.append(f"Position {i}: '{char1}' -> '{char2}'")
        
        # Längenänderungen (0-Regel)
        if len(orig_clean) != len(corrected):
            substitutions.append(f"0-Regel angewendet: Länge {len(orig_clean)} -> {len(corrected)}")
        
        return "; ".join(substitutions) if substitutions else "Keine Änderungen"
    
    def get_corrections_summary(self):
        """Gibt eine Zusammenfassung aller Korrekturen zurück."""
        return self.corrections_made