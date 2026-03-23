#!/usr/bin/env python3
"""Full prescription parsing for Hour 2"""
import json
import sys
sys.path.insert(0, r'd:\projects\PrescriptionNLP\layer_1')
from basic_parser import extract_prescription_fields

# Read input JSON
with open(r'd:\projects\PrescriptionNLP\prescription_raw_text_only.json', 'r') as f:
    data = json.load(f)

print(f"Processing {len(data)} prescriptions...")

# Parse each prescription
results = []
for i, item in enumerate(data):
    raw_text = item.get('raw_text', '')
    parsed = extract_prescription_fields(raw_text)
    results.append(parsed)
    if (i + 1) % 1000 == 0:
        print(f"  Processed {i + 1} prescriptions...")

print(f"Completed! Saving to advanced_output.json...")

# Save to file
with open(r'd:\projects\PrescriptionNLP\layer_2\advanced_output.json', 'w') as f:
    json.dump(results, f, indent=2)

print("Done!")

# Calculate null counts
fields = ['medicine_name', 'form', 'strength', 'dosage', 'frequency', 'duration', 'notes']
print("\n" + "=" * 70)
print("NULL COUNT SUMMARY")
print("=" * 70)
print(f"{'Field':<20} | {'Null Count':<12} | {'Null %':<8}")
print("-" * 70)

for field in fields:
    null_count = sum(1 for r in results if r.get(field) is None)
    null_percent = (null_count / len(results)) * 100
    print(f"{field:<20} | {null_count:<12} | {null_percent:>6.2f}%")

print("=" * 70)
print(f"\nTotal records processed: {len(results)}")
