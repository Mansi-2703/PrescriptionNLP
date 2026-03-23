#!/usr/bin/env python3
"""Test 8 specific cases for Hour 2"""
import json
from parser import extract_prescription_fields

tests = [
    'Atorva 20 mg OD x7d at bedtime',
    'Cal Carb 500MG BD aft fd for 5 days',
    'TAB Metfromin 850 mg 2 tablets BD aftr meals for 7d',
    'Ome40mg OD ac',
    'Paracitamol 1000 mg 1 tablet SOS x3d a/f',
    'Inj Panto 40 mg 1 vial OD in AM for 14 days',
    'Tab Domperidone 10 mg 1 tablet TDS x1wk 30 min before meals',
    'SUSP Ibuprofin100 mgs/5 ml5 ml SOS aft meals x14 days'
]

print("=" * 90)
print("HOUR 2 - 8 TEST CASES")
print("=" * 90)

for i, test in enumerate(tests, 1):
    print(f'\nTest {i}: "{test}"')
    print("-" * 90)
    result = extract_prescription_fields(test)
    print(json.dumps(result, indent=2))

print("\n" + "=" * 90)
