"""
Analysis Script for Layer 4 Evaluation
"""
import json

# Load output
data = json.load(open('lintegrated_final_output.json'))

# Analyze records
perfect_records = []
good_records = []  # 1-2 nulls
partial_records = []  # 3-4 nulls
poor_records = []  # 5+ nulls

required_fields = ['medicine_name', 'strength', 'dosage', 'frequency', 'duration']

for i, record in enumerate(data):
    null_count = sum(1 for field in required_fields if record.get(field) is None)
    
    if null_count == 0:
        perfect_records.append((i, record))
    elif null_count <= 2:
        good_records.append((i, record))
    elif null_count <= 4:
        partial_records.append((i, record))
    else:
        poor_records.append((i, record))

print(f"Total Records: {len(data)}")
print(f"Perfect (0 nulls): {len(perfect_records)}")
print(f"Good (1-2 nulls): {len(good_records)}")
print(f"Partial (3-4 nulls): {len(partial_records)}")
print(f"Poor (5+ nulls): {len(poor_records)}")
print(f"\nAccuracy: {(len(perfect_records) + len(good_records)) / len(data) * 100:.1f}%")

# Print some examples
print("\n" + "="*80)
print("EXAMPLE: PERFECT EXTRACTION")
print("="*80)
if perfect_records:
    idx, rec = perfect_records[0]
    print(f"Raw: {rec['raw_text']}")
    print(f"Medicine: {rec['medicine_name']}")
    print(f"Form: {rec['form']}")
    print(f"Strength: {rec['strength']}")
    print(f"Dosage: {rec['dosage']}")
    print(f"Frequency: {rec['frequency']}")
    print(f"Duration: {rec['duration']}")
    print(f"Notes: {rec['notes']}")

print("\n" + "="*80)
print("EXAMPLE: FAILURE CASE")
print("="*80)
if partial_records:
    idx, rec = partial_records[0]
    print(f"Raw: {rec['raw_text']}")
    nulls = [f for f in required_fields if rec.get(f) is None]
    print(f"Missing fields: {nulls}")
    for field in ['medicine_name', 'form', 'strength', 'dosage', 'frequency', 'duration', 'notes']:
        print(f"{field}: {rec.get(field)}")
