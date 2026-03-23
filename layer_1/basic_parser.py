import json
import re

# ============================================================================
# MEDICINE NAME ALIAS DICTIONARY - Case insensitive lookup
# ============================================================================
MEDICINE_ALIASES = {
    # Antibiotics
    'azithro': 'Azithromycin',
    'azitromycin': 'Azithromycin',
    'azithromycin': 'Azithromycin',
    'doxy': 'Doxycycline',
    'doxycyclene': 'Doxycycline',
    'doxycyclin': 'Doxycycline',
    'doxycycline': 'Doxycycline',
    'cipro': 'Ciprofloxacin',
    'ciprofloxacin': 'Ciprofloxacin',
    'clari': 'Clarithromycin',
    'clarithomycin': 'Clarithromycin',
    'clarithromycin': 'Clarithromycin',
    'cephal': 'Cephalexin',
    'cephalexin': 'Cephalexin',
    'amox': 'Amoxicillin',
    'amoxicillin': 'Amoxicillin',
    'metro': 'Metronidazole',
    'metronidazole': 'Metronidazole',
    'clinda': 'Clindamycin',
    'clindamycin': 'Clindamycin',
    
    # Cardiac / BP
    'atorva': 'Atorvastatin',
    'atorvasttin': 'Atorvastatin',
    'atorvastatin': 'Atorvastatin',
    'lozartan': 'Losartan',
    'losartan k': 'Losartan',
    'losartan': 'Losartan',
    'amlodipne': 'Amlodipine',
    'amlodipine': 'Amlodipine',
    'ramipril': 'Ramipril',
    
    # GI
    'ome': 'Omeprazole',
    'ome40': 'Omeprazole',
    'omeprazole': 'Omeprazole',
    'panto': 'Pantoprazole',
    'pantoprazole': 'Pantoprazole',
    'dom': 'Domperidone',
    'domperidone': 'Domperidone',
    'domperidne': 'Domperidone',
    'ranitidine': 'Ranitidine',
    'raniti': 'Ranitidine',
    
    # CNS / Pain
    'monte': 'Montelukast',
    'montelukast': 'Montelukast',
    'montelucast': 'Montelukast',
    'pregabaln': 'Pregabalin',
    'pregabaline': 'Pregabalin',
    'pregabalin': 'Pregabalin',
    'gaba': 'Gabapentin',
    'gabapentiin': 'Gabapentin',
    'gabapentin': 'Gabapentin',
    'trama': 'Tramadol',
    'tramadol': 'Tramadol',
    'amitrypt': 'Amitriptyline',
    'amitriptyline': 'Amitriptyline',
    'clonazapam': 'Clonazepam',
    'clonazepam': 'Clonazepam',
    'levetira': 'Levetiracetam',
    'levetiracetam': 'Levetiracetam',
    
    # Diabetes
    'metfromin': 'Metformin',
    'metfornin': 'Metformin',
    'metformin': 'Metformin',
    'glicla': 'Gliclazide',
    'gliclazde': 'Gliclazide',
    'gliclazide': 'Gliclazide',
    'glipizide': 'Glipizide',
    'sitaglip': 'Sitagliptin',
    'sitagliptin': 'Sitagliptin',
    
    # Allergy / Respiratory
    'fexofenadin': 'Fexofenadine',
    'fexofenadine': 'Fexofenadine',
    'cetirizne': 'Cetirizine',
    'cetirizine': 'Cetirizine',
    'levocetirizne': 'Levocetirizine',
    'levocetirizine': 'Levocetirizine',
    'salbutamol hfa': 'Salbutamol',
    'salbutamol': 'Salbutamol',
    
    # Pain / Anti-inflammatory
    'naproxene': 'Naproxen',
    'napoxen': 'Naproxen',
    'naproxen': 'Naproxen',
    'ibuprofin': 'Ibuprofen',
    'ibu': 'Ibuprofen',
    'ibuprofen': 'Ibuprofen',
    'aspiirin': 'Aspirin',
    'aspirin': 'Aspirin',
    'mefenamic': 'Mefenamic Acid',
    'mefenamic acid': 'Mefenamic Acid',
    'diclof': 'Diclofenac',
    'diclofenac': 'Diclofenac',
    
    # Vitamins / Supplements
    'calcarb': 'Calcium Carbonate',
    'cal carb': 'Calcium Carbonate',
    'calcium carb': 'Calcium Carbonate',
    'calcium carbonate': 'Calcium Carbonate',
    'feso4': 'Ferrous Sulfate',
    'ferrous': 'Ferrous Sulfate',
    'ferrous sulfate': 'Ferrous Sulfate',
    'folic': 'Folic Acid',
    'folic acid': 'Folic Acid',
    'vit. d3': 'Vitamin D3',
    'vit.d3': 'Vitamin D3',
    'vit d3': 'Vitamin D3',
    'vitamin d 3': 'Vitamin D3',
    'vitamin d3': 'Vitamin D3',
    'vitamin d': 'Vitamin D',
    'vit.': 'Vitamin',
    'vit ': 'Vitamin',
    'vit': 'Vitamin',
    'vitamin': 'Vitamin',
    'zn sulfate': 'Zinc Sulfate',
    'zinc sulfate': 'Zinc Sulfate',
    'multivit': 'Multivitamin',
    'multivitamin': 'Multivitamin',
    'mvi': 'Multivitamin',
    'm.v.i': 'Multivitamin',
    
    # Pain / GI
    'pcm': 'Paracetamol',
    'paracitamol': 'Paracetamol',
    'parcetamol': 'Paracetamol',
    'paracet': 'Paracetamol',
    'paracetamol': 'Paracetamol',
    'ondan': 'Ondansetron',
    'ondansetrone': 'Ondansetron',
    'ondansetron': 'Ondansetron',
    'pred': 'Prednisolone',
    'prednisalone': 'Prednisolone',
    'prednisolone': 'Prednisolone',
    'furose': 'Furosemide',
    'furosemide': 'Furosemide',
    'insulin glargine': 'Insulin Glargine',
}

# ============================================================================
# NOTES ABBREVIATION MAPPING
# ============================================================================
NOTES_ABBREVIATIONS = {
    'a/f': 'after food',
    'af': 'after food',
    'aft': 'after food',
    'aftr': 'after food',
    'aft fd': 'after food',
    'aft food': 'after food',
    'aft meals': 'after meals',
    'aftr meals': 'after meals',
    'after fod': 'after food',
    'fod': 'food',  # for context like "after fod"
    'p/c': 'after meals',
    'pc': 'after meals',
    'b4 food': 'before food',
    'b/f': 'before food',
    'bf': 'before food',
    'bef fd': 'before food',
    'bef meals': 'before meals',
    'ac': 'before meals',
    'es': 'empty stomach',
    'emty stomach': 'empty stomach',
    'empty stmch': 'empty stomach',
    'empty stom': 'empty stomach',
    'h/s': 'at bedtime',
    'hs': 'at bedtime',
    'mrng only': 'morning only',
    'in am': 'morning only',
    'prn': 'if needed',
    'if nec': 'if needed',
    'if req': 'if needed',
    'when reqd': 'if needed',
    'plenty of water': 'with plenty of water',
    'with milk': 'with milk',
    'w/ milk': 'with milk',
    'with meals': 'with meals',
    'w/ meals': 'with meals',
}

def split_fused_tokens(text):
    """Split fused tokens like 'Ome40mg' into 'Ome 40 mg'"""
    # IMPORTANT: Preserve vitamin designations like "D3", "B12", "B6" (capital letter followed by digits)
    # Only split when a lowercase letter is followed by a digit
    text = re.sub(r'([a-z])(\d)', r'\1 \2', text)
    # Ensure space between number and unit (but not after vitamin letters)
    # Only split if the digit is not immediately after a single capital letter (like D3, B12)
    text = re.sub(r'(\d)(mg|mcg|IU|ml|g|mEq)\b', r'\1 \2', text, flags=re.IGNORECASE)
    # Normalize slash spacing in liquid strengths: "mg/5ml" → "mg/5 ml"
    text = re.sub(r'(mg|mcg|g)/(\d)', r'\1/\2', text, flags=re.IGNORECASE)
    text = re.sub(r'/(\d+)(ml)', r'/\1 \2', text, flags=re.IGNORECASE)
    # Handle patterns like "5days" (fused number and unit) -> "5 days"
    text = re.sub(r'(\d+)(days?|d\b)', r'\1 \2', text, flags=re.IGNORECASE)
    # Clean up multiple spaces
    text = re.sub(r'\s+', ' ', text)
    return text

def normalize_frequency(freq_str):
    """Normalize frequency abbreviations to standard terms"""
    if not freq_str:
        return None
    freq_lower = freq_str.lower().strip()
    
    # OD (once daily)
    if re.match(r'^(od|once daily|once daily|1-0-0)$', freq_lower, re.IGNORECASE):
        return "OD"
    # BD (twice daily / every 12 hours)
    elif re.match(r'^(bd|twice daily|every 12 hours|1-1-0)$', freq_lower, re.IGNORECASE):
        return "BD"
    # TDS (thrice daily / every 8 hours)
    elif re.match(r'^(tds|thrice daily|every 8 hours|1-1-1)$', freq_lower, re.IGNORECASE):
        return "TDS"
    # QID (four times)
    elif re.match(r'^(qid|four times|qd)$', freq_lower, re.IGNORECASE):
        return "QID"
    # HS (bedtime)
    elif re.match(r'^(hs|h/s|bedtime)$', freq_lower, re.IGNORECASE):
        return "HS"
    # SOS/PRN (as needed)
    elif re.match(r'^(sos|prn|if needed|when required|when reqd|if nec)$', freq_lower, re.IGNORECASE):
        return "SOS"
    # Once weekly
    elif re.match(r'^(once weekly)$', freq_lower, re.IGNORECASE):
        return "once weekly"
    # Once monthly
    elif re.match(r'^(once monthly)$', freq_lower, re.IGNORECASE):
        return "once monthly"
    
    return None

def normalize_duration(duration_str):
    """Normalize duration to readable form"""
    if not duration_str:
        return None
    
    dur_lower = duration_str.lower().strip()
    
    # Days (match "d", "day", "days", "7d", "7 days", "for 7 days", "x7d", "dayss", "5days")
    match = re.search(r'(\d+)\s*days?s?\b', dur_lower)
    if match:
        return f"{match.group(1)} days"
    
    # Days without space (e.g., "5days", "7d")
    match = re.search(r'(\d+)d(?:ays?)?', dur_lower)
    if match:
        return f"{match.group(1)} days"
    
    # Weeks (match "w", "wk", "week", "weeks", "2wk", "2 weeks", "for 2 weeks", "x2wk")
    match = re.search(r'(\d+)\s*w(?:eeks?|k)?', dur_lower)
    if match:
        days = int(match.group(1)) * 7
        if days == 7:
            return "7 days"
        return f"{days} days"
    
    # Months (match "month", "mon", "1 month", "for 1 month", "x1month")
    match = re.search(r'(\d+)\s*(?:months?|mon)', dur_lower)
    if match:
        num = match.group(1)
        # For consistency, could convert to days (30 days per month) or keep as months
        # Based on rules, keep as months for clarity
        return f"{num} month" if num == '1' else f"{num} months"
    
    return None

def normalize_form(form_str):
    """Normalize form/route to standard terms"""
    if not form_str:
        return None
    
    form_lower = form_str.lower().strip()
    
    # Tablet (including "T/" variant)
    if re.match(r'^(tab|t|tb|t/|tablet)\.?$', form_lower):
        return "tablet"
    # Capsule
    elif re.match(r'^(cap|capsule)\.?$', form_lower):
        return "capsule"
    # Injection
    elif re.match(r'^(inj|injection)\.?$', form_lower):
        return "injection"
    # Suspension
    elif re.match(r'^(susp|suspension)\.?$', form_lower):
        return "suspension"
    # Syrup
    elif re.match(r'^(syr|syrup)\.?$', form_lower):
        return "syrup"
    # Drops
    elif re.match(r'^(drops|drop)\.?$', form_lower):
        return "drops"
    
    return None

def resolve_medicine_name(name_str):
    """Resolve brand/short names to generic names and correct typos"""
    if not name_str:
        return None
    
    name_normalized = name_str.strip()
    name_lower = name_normalized.lower()
    
    # Direct match in alias dictionary
    if name_lower in MEDICINE_ALIASES:
        return MEDICINE_ALIASES[name_lower]
    
    # Try partial matching for multi-word names like "Calcium Carb"
    # Split into words and check if any combination is in the dictionary
    words = name_lower.split()
    for i in range(len(words), 0, -1):
        partial = ' '.join(words[:i])
        if partial in MEDICINE_ALIASES:
            return MEDICINE_ALIASES[partial]
    
    # Special handling for medicine names that start with certain prefixes
    # Check if starts with common known prefixes (for Vitamin D3, etc.)
    if name_lower.startswith('vit'):
        return name_normalized.title()
    
    # If not in dictionary, return capitalized as-is
    return name_normalized.title() if name_normalized else None

def extract_prescription_fields(raw_text):
    """Extract structured fields from prescription text"""
    
    # FIX 2: Handle fused tokens FIRST (before form extraction)
    text = split_fused_tokens(raw_text.strip())
    
    # Initialize result
    result = {
        'medicine_name': None,
        'form': None,
        'strength': None,
        'dosage': None,
        'frequency': None,
        'duration': None,
        'notes': None
    }
    
    # Extract form (Tab, Cap, Inj, Susp, Syr, T/, etc.) - must happen BEFORE text normalization
    form_match = re.match(r'^(Tab\.?|Cap\.?|Inj\.?|Susp\.?|Syr\.?|T/|Tb|Drops?|Injectable)\s+', text, re.IGNORECASE)
    form_str = None
    text_remaining = text
    if form_match:
        form_str = form_match.group(1)
        text_remaining = text[form_match.end():]
    
    result['form'] = normalize_form(form_str)
    
    # Extract medicine name
    # Look for pattern: Name (may have words and numbers like "Vitamin D3") followed by strength/number
    name_match = re.match(r'^([A-Za-z0-9\s\.]+?)\s+(\d+(?:\.\d+)?)\s+(?:mg|IU|mcg|g|ml)', text_remaining, re.IGNORECASE)
    medicine_name = None
    if name_match:
        medicine_name = name_match.group(1).strip()
        text_remaining = text_remaining[name_match.end():]
    else:
        # Try to match just medicine name (for cases like "Multivitamin once daily")
        # Include more flexible pattern
        name_match = re.match(r'^([A-Za-z0-9\s\.]+?)\s+(?:once|bd|od|hs|sos|prn|every|for|if|when|at|x\d|OD|BD|TDS|QID|HS)\b', text_remaining, re.IGNORECASE)
        if name_match:
            medicine_name = name_match.group(1).strip()
    
    result['medicine_name'] = resolve_medicine_name(medicine_name)
    
    
    # Extract strength (e.g., "25 mg", "5 mg/5 ml", "1000 IU")
    strength_match = re.search(r'(\d+(?:\.\d+)?)\s*(mg|g|IU|mcg|ml)(?:\s*/\s*(\d+(?:\.\d+)?)\s*(ml))?', text, re.IGNORECASE)
    if strength_match:
        if strength_match.group(4):  # liquid format with denominator
            result['strength'] = f"{strength_match.group(1)} {strength_match.group(2).lower()}/{strength_match.group(3)} {strength_match.group(4).lower()}"
        else:
            unit = strength_match.group(2).upper() if strength_match.group(2).upper() == 'IU' else strength_match.group(2).lower()
            result['strength'] = f"{strength_match.group(1)} {unit}"
    
    # FIX 3: Improved dosage extraction with better patterns
    dosage_match = re.search(
        r'(\d+\.?\d*)\s*(tablet[s]?|tablts|capsule[s]?|ml|units?|ampoule[s]?|vial[s]?)',
        text, re.IGNORECASE
    )
    if dosage_match:
        quantity = float(dosage_match.group(1))
        unit = dosage_match.group(2).lower()
        
        # Normalize typos and forms
        if 'tablts' in unit:
            dosage_unit = 'tablet' if quantity == 1 else 'tablets'
        elif 'tablet' in unit:
            dosage_unit = 'tablet' if quantity == 1 else 'tablets'
        elif 'capsule' in unit:
            dosage_unit = 'capsule' if quantity == 1 else 'capsules'
        elif unit == 'ml':
            dosage_unit = 'ml'
        elif 'unit' in unit:
            dosage_unit = 'units'
        elif 'ampoule' in unit:
            dosage_unit = 'ampoule' if quantity == 1 else 'ampoules'
        elif 'vial' in unit:
            dosage_unit = 'vial' if quantity == 1 else 'vials'
        else:
            dosage_unit = unit.rstrip('s') if unit.endswith('s') and quantity == 1 else unit
        
        result['dosage'] = f"{dosage_match.group(1)} {dosage_unit}"
    
    # Extract frequency
    # First try standard frequency patterns
    freq_match = re.search(r'\b(OD|BD|TDS|QID|HS|SOS|PRN|once daily|twice daily|thrice daily|every \d+ hours|every \d+hours|1-0-0|1-1-0|1-1-1|1-0-1|once weekly|once monthly)\b', text, re.IGNORECASE)
    if freq_match:
        result['frequency'] = normalize_frequency(freq_match.group(1))
    else:
        # Check for pattern like "every 12 hours"
        if 'every 12 hours' in text.lower() or 'every 12hours' in text.lower():
            result['frequency'] = 'BD'
        elif 'every 8 hours' in text.lower() or 'every 8hours' in text.lower():
            result['frequency'] = 'TDS'
    
    # Extract duration
    # Look for patterns like "x7d", "for 7 days", "x 1wk", "x2wk", "for 1 month", "7 Days", etc.
    # Updated to capture both "for X days" and just "X days", "X Days"
    duration_match = re.search(r'(?:for|x)?\s*(\d+)\s*(?:days?s?|d(?:ays)?|weeks?|wks?|w(?:eeks)?|months?|mon(?:ths)?)\b', text, re.IGNORECASE)
    if duration_match:
        matched = duration_match.group(0)
        result['duration'] = normalize_duration(matched)
    
    # FIX 4: Improved notes extraction with abbreviation normalization
    notes_list = []
    text_lower = text.lower()
    
    # First, extract clinical instructions like "for nerve pain", "for headache", etc.
    # Look for "for <clinical condition>" that appears anywhere in the text
    clinical_matches = re.findall(r'\bfor\s+([a-z][a-z\s]*?)(?:\s+(?:x\d|for|\d+\s+days?)|$)', text_lower)
    for clinical_note in clinical_matches:
        clinical_note = clinical_note.strip()
        # Avoid capturing duration patterns and generic text
        if (not re.match(r'^\d+', clinical_note) and  # doesn't start with number
            'day' not in clinical_note and 'week' not in clinical_note and  # not a duration
            len(clinical_note) > 2):  # not too short
            formatted_note = f"for {clinical_note}"
            notes_list.append(formatted_note)
    
    # Check for abbreviations in NOTES_ABBREVIATIONS mapping (longest first to avoid partial matches)
    sorted_abbrevs = sorted(NOTES_ABBREVIATIONS.items(), key=lambda x: len(x[0]), reverse=True)
    
    # Track which expansions we've already added to avoid duplicates
    added_expansions = set(notes_list)
    
    for abbrev, expansion in sorted_abbrevs:
        if abbrev in text_lower and expansion not in added_expansions:
            # Special handling: if we already have "after meals", skip "after food"
            if expansion == 'after food' and ('after meals' in added_expansions or 'food' in added_expansions):
                continue
            if expansion == 'after meals' and 'after food' in added_expansions:
                continue
            if expansion == 'food':  # Skip standalone "food" - it's usually a typo context
                continue
            if expansion == 'before meals' and 'after food' in added_expansions:  # conflicting instructions
                continue
            notes_list.append(expansion)
            added_expansions.add(expansion)
    
    # Also check for "30 min before meals" pattern
    if '30' in text_lower and 'min' in text_lower and 'before' in text_lower and 'meals' in text_lower:
        if '30 min before meals' not in added_expansions:
            notes_list.append('30 min before meals')
            added_expansions.add('30 min before meals')
    
    # Remove duplicates while preserving order
    notes_list = list(dict.fromkeys(notes_list))
    
    if notes_list:
        result['notes'] = ', '.join(notes_list)
    
    return result

if __name__ == '__main__':
    # Read input JSON
    with open(r'd:\projects\PrescriptionNLP\prescription_raw_text_only.json', 'r') as f:
        data = json.load(f)

    # Parse each prescription
    results = []
    for item in data:
        raw_text = item.get('raw_text', '')
        parsed = extract_prescription_fields(raw_text)
        results.append(parsed)

    # Output JSON
    print(json.dumps(results, indent=2))
