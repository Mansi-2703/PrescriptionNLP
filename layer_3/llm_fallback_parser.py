"""
Hour 3: LLM Fallback Parser using Google Gemini API
Intelligent clinical prescription parser with rule-based + Gemini fallback
"""

import json
import re
import time
import google.generativeai as genai
from typing import Optional, Dict, List
from datetime import datetime, timedelta

# Configure Gemini API
GEMINI_API_KEY = "AIzaSyDwqakxfkDBkthnwZ6gkS6TndB_SI6wGN0"
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash-lite')  # Fastest free tier

# ==================== RATE LIMITING ====================
# Free tier limits: 2 req/min, 50 req/day
class RateLimiter:
    """Prevent API quota exhaustion"""
    def __init__(self, max_per_minute=2, max_per_day=50):
        self.max_per_minute = max_per_minute
        self.max_per_day = max_per_day
        self.requests_minute = []
        self.requests_day = []
        self.last_request_time = None
    
    def can_request(self):
        """Check if we can make a request without violating limits"""
        now = datetime.now()
        
        # Remove old entries (older than 1 minute and 1 day)
        self.requests_minute = [t for t in self.requests_minute if now - t < timedelta(minutes=1)]
        self.requests_day = [t for t in self.requests_day if now - t < timedelta(days=1)]
        
        # Check limits
        if len(self.requests_minute) >= self.max_per_minute:
            return False, f"Minute limit reached ({self.max_per_minute}). Wait 60 seconds."
        
        if len(self.requests_day) >= self.max_per_day:
            return False, f"Daily limit reached ({self.max_per_day}). Wait until tomorrow."
        
        return True, "OK"
    
    def record_request(self):
        """Record a successful API request"""
        now = datetime.now()
        self.requests_minute.append(now)
        self.requests_day.append(now)
        self.last_request_time = now
    
    def wait_if_needed(self):
        """Wait before next request to respect rate limits"""
        if self.last_request_time:
            elapsed = (datetime.now() - self.last_request_time).total_seconds()
            # 2 requests/minute = 30 seconds apart
            wait_time = max(0, 30 - elapsed)
            if wait_time > 0:
                time.sleep(wait_time)
    
    def get_status(self):
        """Get current quota status"""
        return {
            'requests_this_minute': len(self.requests_minute),
            'requests_today': len(self.requests_day),
            'minute_limit': self.max_per_minute,
            'daily_limit': self.max_per_day,
            'remaining_today': self.max_per_day - len(self.requests_day)
        }

rate_limiter = RateLimiter(max_per_minute=2, max_per_day=50)

# SAFETY: Stop using API if quota gets too low
EMERGENCY_STOP_THRESHOLD = 10  # Stop at 10 requests remaining (safety margin)

# Expanded alias dictionary (from layer_2)
MEDICINE_ALIASES = {
    # Antibiotics
    "azithro": "Azithromycin",
    "azitromycin": "Azithromycin",
    "doxy": "Doxycycline",
    "doxycyclene": "Doxycycline",
    "cipro": "Ciprofloxacin",
    "amox": "Amoxicillin",
    "metro": "Metronidazole",
    
    # Cardiac/BP
    "atorva": "Atorvastatin",
    "lozartan": "Losartan",
    "amlodipne": "Amlodipine",
    "ramipril": "Ramipril",
    
    # GI
    "ome": "Omeprazole",
    "panto": "Pantoprazole",
    "dom": "Domperidone",
    
    # CNS/Pain
    "monte": "Montelukast",
    "pregabaln": "Pregabalin",
    "trama": "Tramadol",
    "amitript": "Amitriptyline",
    "clonazapam": "Clonazepam",
    
    # Diabetes
    "metfromin": "Metformin",
    "metfornin": "Metformin",
    "glicla": "Gliclazide",
    
    # Vitamins
    "calcarb": "Calcium Carbonate",
    "feso4": "Ferrous Sulfate",
    "vit d3": "Vitamin D3",
    
    # Pain/Anti-inflammatory
    "naproxene": "Naproxen",
    "ibuprofin": "Ibuprofen",
    "ibu": "Ibuprofen",
    "diclof": "Diclofenac",
    "aspiirin": "Aspirin",
    
    # Common
    "pcm": "Paracetamol",
    "paracitamol": "Paracetamol",
    "ondan": "Ondansetron",
    "pred": "Prednisolone",
    "ranitidine": "Ranitidine",
}

# Notes abbreviation mappings
NOTES_MAPPINGS = {
    "a/f": "after food",
    "af": "after food",
    "aft": "after food",
    "aft fd": "after food",
    "after fod": "after food",
    "p/c": "after meals",
    "pc": "after meals",
    "b/f": "before food",
    "bf": "before food",
    "ac": "before meals",
    "es": "empty stomach",
    "emty stomach": "empty stomach",
    "h/s": "at bedtime",
    "hs": "at bedtime",
    "mrng only": "morning only",
    "in am": "morning only",
    "prn": "if needed",
    "if nec": "if needed",
}

def split_fused_tokens(text: str) -> str:
    """Split fused letters and numbers: Ome40mg → Ome 40 mg"""
    text = re.sub(r'([A-Za-z])(\d)', r'\1 \2', text)
    text = re.sub(r'(\d)(mg|mcg|IU|ml|g)', r'\1 \2', text, flags=re.IGNORECASE)
    text = re.sub(r'/(\d+)(ml)', r'/\1 \2', text, flags=re.IGNORECASE)
    return text

def resolve_medicine_name(name: Optional[str]) -> Optional[str]:
    """Resolve brand/short names to generic names"""
    if not name:
        return None
    
    name_lower = name.lower().strip()
    if name_lower in MEDICINE_ALIASES:
        return MEDICINE_ALIASES[name_lower]
    
    return name.title() if name else None

def normalize_frequency(freq: Optional[str]) -> Optional[str]:
    """Normalize frequency abbreviations"""
    if not freq:
        return None
    
    freq_lower = freq.lower().strip()
    freq_map = {
        'od': 'OD', 'once daily': 'OD',
        'bd': 'BD', 'twice daily': 'BD',
        'tds': 'TDS', 'thrice daily': 'TDS',
        'qid': 'QID', 'four times': 'QID',
        'hs': 'HS', 'bedtime': 'HS',
        'sos': 'SOS', 'prn': 'SOS',
    }
    return freq_map.get(freq_lower, freq.upper() if freq_lower in ['od', 'bd', 'tds', 'qid', 'hs', 'sos'] else None)

def normalize_duration(dur: Optional[str]) -> Optional[str]:
    """Normalize duration: x7d → 7 days"""
    if not dur:
        return None
    
    dur_lower = dur.lower()
    
    # Days
    match = re.search(r'(\d+)\s*d(?:ays?)?', dur_lower)
    if match:
        return f"{match.group(1)} days"
    
    # Weeks
    match = re.search(r'(\d+)\s*w(?:eeks?|k)?', dur_lower)
    if match:
        return f"{match.group(1)} week" if match.group(1) == '1' else f"{match.group(1)} weeks"
    
    # Months
    match = re.search(r'(\d+)\s*(?:months?|mon)', dur_lower)
    if match:
        return f"{match.group(1)} month" if match.group(1) == '1' else f"{match.group(1)} months"
    
    return None

def normalize_notes(text: str) -> Optional[str]:
    """Normalize notes and abbreviations"""
    if not text:
        return None
    
    notes_list = []
    text_lower = text.lower()
    
    # Check each mapping
    for abbr, full in NOTES_MAPPINGS.items():
        if re.search(r'\b' + re.escape(abbr) + r'\b', text_lower, re.IGNORECASE):
            if full not in notes_list:
                notes_list.append(full)
    
    # Special phrases
    if re.search(r'30\s+min\s+before\s+meals?', text_lower):
        if "30 min before meals" not in notes_list:
            notes_list.append("30 min before meals")
    
    if 'plenty of water' in text_lower:
        if 'with plenty of water' not in notes_list:
            notes_list.append('with plenty of water')
    
    return ", ".join(notes_list) if notes_list else None

def rule_based_extract(text: str) -> Dict:
    """Rule-based extraction (from layer_2)"""
    text = split_fused_tokens(text)
    
    result = {
        'medicine_name': None,
        'form': None,
        'strength': None,
        'dosage': None,
        'frequency': None,
        'duration': None,
        'notes': None
    }
    
    # Extract form
    form_match = re.match(r'^(tab|cap|inj|susp|syr|drops?|cream|gel|inhaler)[\.\s]+', text, re.IGNORECASE)
    if form_match:
        form_text = form_match.group(1).lower()
        form_map = {'tab': 'tablet', 'cap': 'capsule', 'inj': 'injection', 'susp': 'suspension', 'syr': 'syrup'}
        result['form'] = form_map.get(form_text, form_text)
        text = text[form_match.end():]
    
    # Extract medicine name
    name_match = re.match(r'^([A-Za-z0-9\s]+?)\s+(\d+)', text)
    if name_match:
        result['medicine_name'] = resolve_medicine_name(name_match.group(1).strip())
    
    # Extract strength
    strength_match = re.search(r'(\d+\.?\d*)\s*(mg|mcg|IU|g)(?:/(\d+)\s*ml)?', text, re.IGNORECASE)
    if strength_match:
        if strength_match.group(3):
            result['strength'] = f"{strength_match.group(1)}{strength_match.group(2).lower()}/{strength_match.group(3)}ml"
        else:
            result['strength'] = f"{strength_match.group(1)}{strength_match.group(2).lower()}"
    
    # Extract dosage
    dosage_match = re.search(r'(\d+\.?\d*)\s*(tablet|tablets|capsule|capsules|ml|units?|vial|vials|ampoule|ampoules)', text, re.IGNORECASE)
    if dosage_match:
        qty = dosage_match.group(1)
        unit = dosage_match.group(2).lower()
        if 'tablet' in unit:
            result['dosage'] = f"{qty} tablet" if qty == '1' else f"{qty} tablets"
        elif 'capsule' in unit:
            result['dosage'] = f"{qty} capsule" if qty == '1' else f"{qty} capsules"
        elif unit == 'ml':
            result['dosage'] = f"{qty}ml"
        elif 'unit' in unit:
            result['dosage'] = f"{qty} units"
        elif 'vial' in unit:
            result['dosage'] = f"{qty} vial" if qty == '1' else f"{qty} vials"
        elif 'ampoule' in unit:
            result['dosage'] = f"{qty} ampoule" if qty == '1' else f"{qty} ampoules"
        else:
            result['dosage'] = f"{qty} {unit}"
    
    # Extract frequency
    freq_match = re.search(r'\b(OD|BD|TDS|QID|HS|SOS|once daily|twice daily)\b', text, re.IGNORECASE)
    if freq_match:
        result['frequency'] = normalize_frequency(freq_match.group(1))
    
    # Extract duration - handle x1wk, x7d, for 5 days, etc.
    dur_match = re.search(r'(?:for|x)\s*(\d+)\s*(?:days?|d|weeks?|wks?|w|months?|mon)\b', text, re.IGNORECASE)
    if not dur_match:
        # Try without space: x1wk, x5d
        dur_match = re.search(r'(?:for|x)(\d+)(?:days?|d|weeks?|wks?|w|months?|mon)\b', text, re.IGNORECASE)
    
    if dur_match:
        result['duration'] = normalize_duration(dur_match.group(0))
    
    # Extract notes
    result['notes'] = normalize_notes(text)
    
    return result

def extract_with_gemini(text: str) -> Dict:
    """Use Gemini API for intelligent extraction with AGGRESSIVE rate limiting"""
    # Check rate limits BEFORE making request
    can_request, msg = rate_limiter.can_request()
    
    if not can_request:
        print(f"[API RATE LIMIT] {msg}")
        print(f"[API STATUS] {rate_limiter.get_status()}")
        return None
    
    # EMERGENCY STOP: Refuse if quota is getting low
    status = rate_limiter.get_status()
    remaining = status['remaining_today']
    
    if remaining <= EMERGENCY_STOP_THRESHOLD:
        print(f"[EMERGENCY STOP] API quota critical ({remaining} remaining)!")
        print(f"[EMERGENCY STOP] Stopping all API calls to preserve quota")
        print(f"[STATUS] {status}")
        return None
    
    if remaining <= 15:
        print(f"[WARNING] API quota low: {remaining} requests remaining (stop at {EMERGENCY_STOP_THRESHOLD})")
    
    prompt = f"""
You are a clinical prescription parser specializing in Indian prescription text. 
Extract structured data from this prescription:

"{text}"

Return ONLY a valid JSON object with these exact keys:
- medicine_name (generic name, resolve aliases)
- form (tablet, capsule, injection, syrup, suspension, drops, cream, gel, or inhaler)
- strength (e.g., "500mg", "100mg/5ml")
- dosage (e.g., "1 tablet", "5ml")
- frequency (OD, BD, TDS, QID, HS, or SOS only)
- duration (e.g., "7 days", "1 week")
- notes (e.g., "after food", "before meals", "at bedtime")

Use null for any field that cannot be determined.
Handle typos and abbreviations intelligently.

JSON:
"""
    
    try:
        # Wait if needed to respect rate limits (30 sec between requests)
        rate_limiter.wait_if_needed()
        
        response = model.generate_content(prompt)
        json_text = response.text.strip()
        
        # Record successful API call
        rate_limiter.record_request()
        status = rate_limiter.get_status()
        print(f"[API CALL SUCCESS] Remaining today: {status['remaining_today']}/{status['daily_limit']}")
        
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', json_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
    except Exception as e:
        error_msg = str(e)
        print(f"[Gemini API error] {error_msg[:100]}")
        
        # Check if it's a quota error
        if "429" in error_msg or "quota" in error_msg.lower():
            print(f"[QUOTA EXCEEDED] Daily limit hit. Current status: {rate_limiter.get_status()}")
    
    return None

def hybrid_extract(text: str, use_gemini: bool = True) -> Dict:
    """
    Hybrid extraction: Rules first, then Gemini fallback (ULTRA CONSERVATIVE)
    
    Only uses Gemini for EXTREME cases where multiple critical fields are missing
    This protects the API quota aggressively
    
    Parameters:
    - text: prescription text
    - use_gemini: if True, use Gemini ONLY for extreme edge cases
    """
    # First attempt: rule-based extraction
    result = rule_based_extract(text)
    
    # Count critical missing fields (not form/notes which are less critical)
    critical_fields = ['medicine_name', 'strength', 'dosage', 'frequency']
    critical_nulls = sum(1 for k in critical_fields if result.get(k) is None)
    
    # ULTRA CONSERVATIVE: Only use Gemini if ALL critical fields are missing
    # This means the prescription is completely unparseable
    use_api = use_gemini and critical_nulls >= 4 and result['medicine_name'] is None
    
    if use_api:
        try:
            gemini_result = extract_with_gemini(text)
            if gemini_result:
                # Merge: use Gemini for missing fields
                for key in result:
                    if result[key] is None and gemini_result.get(key) is not None:
                        result[key] = gemini_result[key]
                # Mark if Gemini was used
                result['_llm_fallback'] = True
        except:
            pass
    
    return result

def parse_batch(prescriptions: List[Dict], use_gemini: bool = False) -> List[Dict]:
    """
    Parse batch of prescriptions
    
    DEFAULT: use_gemini=False to prevent quota exhaustion
    Only enable Gemini if you have verified quota available
    """
    if use_gemini:
        print("[WARNING] Gemini fallback ENABLED - monitor quota carefully")
        print(f"[WARNING] Rate limits: 2 req/min, 50 req/day")
    else:
        print("[INFO] Gemini fallback DISABLED - using rule-based only (safe, no API costs)")
    
    results = []
    for i, item in enumerate(prescriptions):
        raw_text = item.get('raw_text', '')
        try:
            parsed = hybrid_extract(raw_text, use_gemini=use_gemini)
            results.append(parsed)
            if (i + 1) % 100 == 0:
                print(f"Processed {i + 1} records...")
        except Exception as e:
            print(f"Error parsing: {raw_text[:50]}... - {e}")
            results.append({
                'medicine_name': None,
                'form': None,
                'strength': None,
                'dosage': None,
                'frequency': None,
                'duration': None,
                'notes': None,
                '_error': str(e)
            })
    
    return results

def validate_json(result: Dict) -> bool:
    """Validate extraction result"""
    required_keys = {'medicine_name', 'form', 'strength', 'dosage', 'frequency', 'duration', 'notes'}
    return set(result.keys()) >= required_keys

# Main execution
if __name__ == "__main__":
    print("Loading prescription data...")
    with open('../prescription_raw_text_only.json', 'r') as f:
        data = json.load(f)
    
    print(f"Parsing {len(data)} prescriptions with hybrid extraction...")
    results = parse_batch(data, use_gemini=True)
    
    print("\nValidating results...")
    valid_count = sum(1 for r in results if validate_json(r))
    print(f"Valid records: {valid_count}/{len(results)}")
    
    # Save output
    output_file = 'llm_fallback_output.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to {output_file}")
    
    # Print summary
    null_counts = {}
    for key in ['medicine_name', 'form', 'strength', 'dosage', 'frequency', 'duration', 'notes']:
        null_count = sum(1 for r in results if r.get(key) is None)
        null_pct = (null_count / len(results)) * 100
        null_counts[key] = (null_count, null_pct)
        print(f"{key:20s} | {null_count:5d} | {null_pct:6.2f}%")
    
    # Count Gemini usage
    gemini_count = sum(1 for r in results if r.get('_llm_fallback'))
    print(f"\nGemini fallback used: {gemini_count} records ({(gemini_count/len(results))*100:.2f}%)")
