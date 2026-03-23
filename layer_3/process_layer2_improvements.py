#!/usr/bin/env python3
"""
Layer 3: Smart Hybrid Processing
- LOADS Layer 2 output as input
- IDENTIFIES records with >3 null values (complex cases)
- APPLIES improved hybrid extraction only to complex cases
- KEEPS Layer 2 results for well-extracted records (<=3 nulls)
"""

import json
import sys
sys.path.insert(0, r'd:\projects\PrescriptionNLP\layer_1')
sys.path.insert(0, r'd:\projects\PrescriptionNLP\layer_3')

from basic_parser import extract_prescription_fields
from llm_fallback_parser import hybrid_extract

def count_nulls(record):
    """Count null values in a prescription record"""
    return sum(1 for k, v in record.items() 
               if k not in ['_llm_fallback', '_error'] and v is None)

def main():
    print("=" * 100)
    print("LAYER 3: SMART HYBRID IMPROVEMENT")
    print("Input: Layer 2 output | Processing: Complex cases only")
    print("=" * 100)
    
    # Load Layer 2 output
    print("\n1. Loading Layer 2 output...")
    try:
        with open(r'd:\projects\PrescriptionNLP\layer_2\advanced_output.json', 'r') as f:
            layer2_results = json.load(f)
        print(f"   ✓ Loaded {len(layer2_results)} prescriptions from Layer 2")
    except FileNotFoundError:
        print("   ✗ Error: Layer 2 output not found")
        return
    
    # Load raw text for complex cases
    print("\n2. Loading raw prescription text...")
    try:
        with open(r'd:\projects\PrescriptionNLP\prescription_raw_text_only.json', 'r') as f:
            raw_data = json.load(f)
        print(f"   ✓ Loaded {len(raw_data)} raw prescriptions")
    except FileNotFoundError:
        print("   ✗ Error: Raw prescription data not found")
        return
    
    # Identify complex cases
    print("\n3. Identifying complex cases (>3 null values)...")
    complex_cases = []
    for i, record in enumerate(layer2_results):
        nulls = count_nulls(record)
        if nulls > 3:
            complex_cases.append({
                'index': i,
                'nulls': nulls,
                'raw_text': raw_data[i].get('raw_text', ''),
                'layer2_result': record
            })
    
    print(f"   ✓ Found {len(complex_cases)} complex cases ({len(complex_cases)/len(layer2_results)*100:.2f}%)")
    print(f"   ✓ Found {len(layer2_results) - len(complex_cases)} well-extracted records (keeping as-is)")
    
    # Process complex cases with improved hybrid extraction
    print(f"\n4. Processing complex cases with improved extraction...")
    print(f"   (Using rule-based improvements, Gemini fallback DISABLED for quota protection)")
    
    improved_count = 0
    total_improvement = 0
    
    for case in complex_cases:
        raw_text = case['raw_text']
        layer2_nulls = case['nulls']
        
        # Apply improved extraction (rule-based enhanced version)
        improved_result = extract_prescription_fields(raw_text)
        improved_nulls = count_nulls(improved_result)
        
        # Check if improved
        if improved_nulls < layer2_nulls:
            improved_count += 1
            total_improvement += (layer2_nulls - improved_nulls)
            case['improved'] = True
            case['improvement'] = layer2_nulls - improved_nulls
            case['new_result'] = improved_result
        else:
            case['improved'] = False
            case['new_result'] = case['layer2_result']  # Keep Layer 2 result
    
    print(f"   ✓ Improved {improved_count}/{len(complex_cases)} complex cases")
    print(f"   ✓ Total fields improved: {total_improvement}")
    
    # Build Layer 3 output
    print(f"\n5. Building Layer 3 output (merging improvements with Layer 2)...")
    layer3_results = []
    
    for i, layer2_record in enumerate(layer2_results):
        # Check if this is a complex case that was improved
        matching_case = next((c for c in complex_cases if c['index'] == i), None)
        
        if matching_case:
            # Use improved result if available
            layer3_results.append(matching_case['new_result'])
        else:
            # Keep Layer 2 result for well-extracted cases
            layer3_results.append(layer2_record)
    
    print(f"   ✓ Built Layer 3 output with {len(layer3_results)} records")
    
    # Calculate improvement metrics
    print(f"\n6. Calculating improvement metrics...")
    
    fields = ['medicine_name', 'form', 'strength', 'dosage', 'frequency', 'duration', 'notes']
    
    print(f"\n{'Field':<20} | {'Layer 2 Nulls':<15} | {'Layer 3 Nulls':<15} | {'Improvement':<15}")
    print("-" * 100)
    
    total_nulls_removed = 0
    for field in fields:
        l2_null = sum(1 for r in layer2_results if r.get(field) is None)
        l3_null = sum(1 for r in layer3_results if r.get(field) is None)
        improvement = l2_null - l3_null
        total_nulls_removed += improvement
        print(f"{field:<20} | {l2_null:<15} | {l3_null:<15} | {improvement:+d} ({(improvement/l2_null*100 if l2_null > 0 else 0):>6.1f}%)")
    
    print("-" * 100)
    print(f"TOTAL NULLS REMOVED: {total_nulls_removed}")
    
    # Save Layer 3 output
    print(f"\n7. Saving Layer 3 output...")
    output_file = r'd:\projects\PrescriptionNLP\layer_3\improved_layer2_output.json'
    with open(output_file, 'w') as f:
        json.dump(layer3_results, f, indent=2)
    print(f"   ✓ Saved to improved_layer2_output.json")
    
    # Record-level analysis
    print(f"\n8. Record-level comparison...")
    
    records_with_improvement = 0
    total_per_record_improvement = 0
    
    for i, (l2, l3) in enumerate(zip(layer2_results, layer3_results)):
        l2_nulls = count_nulls(l2)
        l3_nulls = count_nulls(l3)
        if l3_nulls < l2_nulls:
            records_with_improvement += 1
            total_per_record_improvement += (l2_nulls - l3_nulls)
    
    print(f"   Records with improvement: {records_with_improvement}/{len(layer2_results)} ({records_with_improvement/len(layer2_results)*100:.2f}%)")
    print(f"   Avg improvement/record: {total_per_record_improvement/records_with_improvement:.2f} fields" if records_with_improvement > 0 else "   No improvements")
    
    print("\n" + "=" * 100)
    print("LAYER 3 PROCESSING COMPLETE")
    print("=" * 100)
    print(f"\nSummary:")
    print(f"  Input: Layer 2 output (10,000 prescriptions)")
    print(f"  Complex cases identified: {len(complex_cases)} ({len(complex_cases)/len(layer2_results)*100:.2f}%)")
    print(f"  Complex cases improved: {improved_count}/{len(complex_cases)}")
    print(f"  Total fields improved: {total_nulls_removed}")
    print(f"  Output: improved_layer2_output.json")
    print()

if __name__ == "__main__":
    main()
