"""
LAYER 4 - Complete Pipeline Integration
=========================================
Hour 4: Full Dataset Processing with Batch LLM Integration

Workflow:
1. Load all 10,000 raw prescriptions
2. Apply rule-based extraction (Layer 1 enhanced rules)
3. Score confidence (% fields extracted)
4. Identify LOW-CONFIDENCE records (confidence < threshold)
5. Batch process LOW-CONFIDENCE records with Gemini (20 per batch)
6. Merge rule-based + LLM-enhanced results
7. Output comprehensive final JSON

Key Features:
- Batch processing: 20 records per API call (cost/time optimization)
- Confidence scoring: Identifies records needing LLM help
- Rate limiting: 2 req/min, 50 req/day protection
- Emergency stop: Prevents quota exhaustion
- Comprehensive reporting: Statistics and improvement tracking
"""

import json
import time
import os
import sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import re

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️  google-generativeai not installed. Install with: pip install google-generativeai")

from layer_1.basic_parser import extract_prescription_fields

# ============================================================================
# PARSER WRAPPER
# ============================================================================

class BasicPrescriptionParser:
    """Wrapper around extract_prescription_fields for consistent API"""
    def parse(self, raw_text):
        return extract_prescription_fields(raw_text)

# ============================================================================
# RATE LIMITER - Protect API Quota
# ============================================================================

class RateLimiter:
    """Tracks API calls and enforces rate limits"""
    
    def __init__(self, requests_per_minute=2, requests_per_day=50):
        self.rpm = requests_per_minute
        self.rpd = requests_per_day
        self.minute_calls = []
        self.day_calls = []
        self.emergency_stop_threshold = 10
        
    def can_call(self, remaining_quota):
        """Check if API call is allowed"""
        now = time.time()
        
        # Remove old calls outside windows
        self.minute_calls = [t for t in self.minute_calls if now - t < 60]
        self.day_calls = [t for t in self.day_calls if now - t < 86400]
        
        # Check quotas
        if remaining_quota <= self.emergency_stop_threshold:
            print(f"🛑 EMERGENCY STOP: Only {remaining_quota} requests remaining!")
            return False
        
        if len(self.minute_calls) >= self.rpm:
            wait_time = 60 - (now - self.minute_calls[0])
            print(f"⏳ Rate limit (2/min): Waiting {wait_time:.1f}s")
            time.sleep(wait_time)
            self.minute_calls = []
        
        if len(self.day_calls) >= self.rpd:
            print(f"🛑 Daily quota exhausted! ({self.rpd} requests)")
            return False
        
        return True
    
    def record_call(self):
        """Record that an API call was made"""
        now = time.time()
        self.minute_calls.append(now)
        self.day_calls.append(now)

# ============================================================================
# CONFIDENCE SCORER
# ============================================================================

def score_confidence(record):
    """
    Calculate confidence score (0-100) based on field extraction quality
    
    High confidence: Most fields extracted (null_count <= 1)
    Low confidence: Many nulls (null_count >= 3)
    """
    required_fields = ['medicine_name', 'strength', 'dosage', 'frequency', 'duration']
    null_count = sum(1 for field in required_fields if record.get(field) is None)
    
    # Confidence = (fields_extracted / total_fields) * 100
    confidence = ((len(required_fields) - null_count) / len(required_fields)) * 100
    return confidence, null_count

# ============================================================================
# BATCH GEMINI PROCESSOR - Optimized for Cost
# ============================================================================

class BatchGeminiProcessor:
    """
    Processes multiple records per API call
    - Groups 20 low-confidence records per batch
    - Single API call processes entire batch
    - Massive cost/time savings
    """
    
    def __init__(self, api_key=None, batch_size=20):
        self.batch_size = batch_size
        self.rate_limiter = RateLimiter(requests_per_minute=2, requests_per_day=50)
        self.processed_count = 0
        self.improved_count = 0
        
        if GEMINI_AVAILABLE and api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash-lite')
        else:
            self.model = None
    
    def process_batch(self, batch_records, remaining_quota):
        """
        Process a batch of records in single API call
        
        Args:
            batch_records: List of 20 prescription records with null fields
            remaining_quota: API quota remaining
        
        Returns:
            Updated records with Gemini-enhanced fields
        """
        if not self.model or not self.rate_limiter.can_call(remaining_quota):
            return batch_records, 0
        
        # Format batch for Gemini
        batch_text = self._format_batch(batch_records)
        prompt = self._build_prompt(batch_text)
        
        try:
            print(f"📤 Sending batch of {len(batch_records)} records to Gemini...")
            response = self.model.generate_content(prompt)
            self.rate_limiter.record_call()
            
            # Parse response and apply to records
            improvements = self._parse_and_apply(response.text, batch_records)
            self.improved_count += improvements
            
            print(f"✅ Batch processed: +{improvements} improvements")
            return batch_records, improvements
            
        except Exception as e:
            print(f"⚠️  Batch processing failed: {str(e)}")
            return batch_records, 0
    
    def _format_batch(self, records):
        """Format multiple records for Gemini"""
        formatted = []
        for idx, record in enumerate(records, 1):
            formatted.append(f"""
Record {idx} - Raw: {record['raw_text']}
Current Extract: {json.dumps({k: record.get(k) for k in ['medicine_name', 'strength', 'dosage', 'frequency', 'duration']}, indent=2)}
""")
        return "\n".join(formatted)
    
    def _build_prompt(self, batch_text):
        """Build prompt for batch processing"""
        return f"""You are a prescription parser. For each record, fill in the missing null fields:
        
REQUIRED FIELDS: medicine_name, strength, dosage, frequency, duration

Instructions:
1. Extract ONLY from the raw text provided
2. Return JSON for each record with ALL 5 fields
3. Use null for truly missing information

BATCH TO PROCESS:
{batch_text}

RESPONSE FORMAT (JSON array):
[
  {{"record_num": 1, "medicine_name": "...", "strength": "...", "dosage": "...", "frequency": "...", "duration": "..."}},
  {{"record_num": 2, "medicine_name": "...", "strength": "...", "dosage": "...", "frequency": "...", "duration": "..."}}
]

Return ONLY the JSON array, no other text."""
    
    def _parse_and_apply(self, response_text, batch_records):
        """Parse Gemini response and apply updates to records"""
        improvements = 0
        try:
            # Extract JSON from response
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if not json_match:
                return 0
            
            updates = json.loads(json_match.group())
            
            for update in updates:
                record_num = update.get('record_num', 0) - 1
                if 0 <= record_num < len(batch_records):
                    record = batch_records[record_num]
                    for field in ['medicine_name', 'strength', 'dosage', 'frequency', 'duration']:
                        if field in update and update[field] and record.get(field) is None:
                            record[field] = update[field]
                            improvements += 1
        except json.JSONDecodeError:
            pass
        
        return improvements

# ============================================================================
# MAIN LAYER 4 PIPELINE
# ============================================================================

class Layer4Pipeline:
    """Complete end-to-end prescription processing pipeline"""
    
    def __init__(self, api_key=None):
        self.parser = BasicPrescriptionParser()
        self.gemini_processor = BatchGeminiProcessor(api_key=api_key) if api_key else None
        self.statistics = defaultdict(int)
        self.low_confidence_batch = []
        self.all_results = []
        
    def load_raw_data(self, filepath):
        """Load raw prescriptions"""
        print(f"📂 Loading raw prescriptions from {filepath}...")
        with open(filepath, 'r') as f:
            data = json.load(f)
        print(f"✅ Loaded {len(data)} prescriptions\n")
        return data
    
    def process_all_records(self, raw_prescriptions, use_gemini=True):
        """
        Main processing workflow:
        1. Parse all records with rules
        2. Score confidence
        3. Collect low-confidence for batch LLM
        4. Process batches with Gemini
        5. Merge results
        """
        print("="*70)
        print("LAYER 4 - COMPLETE PIPELINE EXECUTION")
        print("="*70 + "\n")
        
        # Stage 1: Rule-Based Parsing
        print("📋 STAGE 1: Rule-Based Extraction (All Records)")
        print("-" * 70)
        
        self.all_results = []
        confidence_scores = []
        low_conf_with_indices = []
        
        for idx, raw_item in enumerate(raw_prescriptions):
            raw_text = raw_item.get('raw_text', '')
            
            # Parse with rule-based engine
            parsed = self.parser.parse(raw_text)
            parsed['raw_text'] = raw_text
            parsed['record_id'] = idx + 1
            
            # Score confidence
            conf, null_cnt = score_confidence(parsed)
            parsed['confidence'] = conf
            parsed['null_count'] = null_cnt
            
            self.all_results.append(parsed)
            confidence_scores.append(conf)
            
            # Collect low-confidence records (confidence < 80%)
            if conf < 80 and use_gemini:
                low_conf_with_indices.append((idx, parsed))
            
            if (idx + 1) % 1000 == 0:
                print(f"  ✓ Processed {idx + 1}/{len(raw_prescriptions)} records")
        
        print(f"✅ Rule-based parsing complete\n")
        
        # Statistics
        avg_conf = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        low_conf_count = sum(1 for c in confidence_scores if c < 80)
        
        print(f"📊 PARSING STATISTICS:")
        print(f"  - Average confidence: {avg_conf:.1f}%")
        print(f"  - Low-confidence records (< 80%): {low_conf_count}")
        print(f"  - Records above 80% confidence: {len(raw_prescriptions) - low_conf_count}\n")
        
        self.statistics['total_records'] = len(raw_prescriptions)
        self.statistics['avg_confidence'] = avg_conf
        self.statistics['low_confidence_count'] = low_conf_count
        
        # Stage 2: Batch Gemini Processing
        if self.gemini_processor and use_gemini and low_conf_with_indices:
            print("🤖 STAGE 2: Batch LLM Processing (Low-Confidence Records)")
            print("-" * 70)
            print(f"  Processing {len(low_conf_with_indices)} low-confidence records\n")
            
            # Create batches of 20
            batch_size = 20
            total_improved = 0
            
            for batch_start in range(0, len(low_conf_with_indices), batch_size):
                batch_end = min(batch_start + batch_size, len(low_conf_with_indices))
                batch_indices_and_records = low_conf_with_indices[batch_start:batch_end]
                batch_records = [r for _, r in batch_indices_and_records]
                batch_indices = [i for i, _ in batch_indices_and_records]
                
                print(f"  📦 Batch {batch_start // batch_size + 1}: Records {batch_start + 1}-{batch_end}")
                
                # Process batch with Gemini
                updated_batch, improvements = self.gemini_processor.process_batch(
                    batch_records, 
                    remaining_quota=42  # Approximate remaining quota
                )
                
                # Apply updates back to results
                for idx_in_batch, record_idx in enumerate(batch_indices):
                    self.all_results[record_idx] = updated_batch[idx_in_batch]
                
                total_improved += improvements
                
                if improvements == 0:
                    print(f"    ⚠️  No improvements from this batch")
            
            print(f"\n✅ LLM Processing Complete: +{total_improved} total improvements")
            self.statistics['llm_improvements'] = total_improved
        else:
            if use_gemini:
                print("⚠️  STAGE 2: Skipped (No Gemini API key or all records high-confidence)\n")
        
        return self.all_results
    
    def save_results(self, output_filepath):
        """Save final output in expected schema format"""
        output_path = Path(output_filepath)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Format output to match expected schema exactly
        # Schema: raw_text, medicine_name, form, strength, dosage, frequency, duration, notes
        clean_results = []
        for record in self.all_results:
            clean_record = {
                'raw_text': record.get('raw_text'),
                'medicine_name': record.get('medicine_name'),
                'form': record.get('form'),
                'strength': record.get('strength'),
                'dosage': record.get('dosage'),
                'frequency': record.get('frequency'),
                'duration': record.get('duration'),
                'notes': record.get('notes')
            }
            clean_results.append(clean_record)
        
        with open(output_path, 'w') as f:
            json.dump(clean_results, f, indent=2)
        
        print(f"💾 Results saved to: {output_filepath}\n")
        return output_path

# ============================================================================
# EXECUTION
# ============================================================================

if __name__ == "__main__":
    # Get API key from environment
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'AIzaSyDwqakxfkDBkthnwZ6gkS6TndB_SI6wGN0')
    
    # Initialize pipeline
    pipeline = Layer4Pipeline(api_key=GEMINI_API_KEY if GEMINI_AVAILABLE else None)
    
    # Load raw data
    raw_data = pipeline.load_raw_data('../prescription_raw_text_only.json')
    
    # Process all records with optional Gemini
    results = pipeline.process_all_records(raw_data, use_gemini=GEMINI_AVAILABLE)
    
    # Save final output
    output_file = 'layer_4_final_output.json'
    pipeline.save_results(output_file)
    
    # Generate Summary Report
    print("="*70)
    print("EXECUTION COMPLETE - LAYER 4 PIPELINE")
    print("="*70)
    print(f"\n📊 FINAL STATISTICS:")
    print(f"  Total Records Processed: {pipeline.statistics.get('total_records', 0)}")
    print(f"  Average Confidence Score: {pipeline.statistics.get('avg_confidence', 0):.1f}%")
    print(f"  Low-Confidence Records (< 80%): {pipeline.statistics.get('low_confidence_count', 0)}")
    print(f"  LLM Improvements: {pipeline.statistics.get('llm_improvements', 0)}")
    print(f"\n📁 Output: {output_file}")
    print("="*70)
