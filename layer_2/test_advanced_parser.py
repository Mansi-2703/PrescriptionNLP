#!/usr/bin/env python3
"""Test script for Hour 2 improvements"""
import json
from parser import extract_prescription_fields

# 8 Test cases from requirements
test_cases = [
    "Atorva 20 mg OD x7d at bedtime",
    "Cal Carb 500MG BD aft fd for 5 days",
    "TAB Metfromin 850 mg 2 tablets BD aftr meals for 7d",
    "Ome40mg OD ac",
    "Paracitamol 1000 mg 1 tablet SOS x3d a/f",
    "Inj Panto 40 mg 1 vial OD in AM for 14 days",
    "Tab Domperidone 10 mg 1 tablet TDS x1wk 30 min before meals",
    "SUSP Ibuprofin100 mgs/5 ml5 ml SOS aft meals x14 days"
]

print("=" * 80)
print("HOUR 2 TEST CASES - Full JSON Output")
print("=" * 80)

for i, test_case in enumerate(test_cases, 1):
    print(f"\n[Test {i}] Input: \"{test_case}\"")
    result = extract_prescription_fields(test_case)
    print(f"Output:\n{json.dumps(result, indent=2)}")
    print("-" * 80)
