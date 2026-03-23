# PrescriptionNLP

## Overall Approach
This project follows a practical hybrid extraction strategy designed for noisy clinical text.

1. Rule-based core parser:
   - Regex-driven extraction for medicine_name, form, strength, dosage, frequency, duration, and notes.
   - Strong preprocessing for fused tokens, spelling noise, abbreviation expansion, and alias normalization.
2. Layered processing architecture:
   - Layer 1 and Layer 2 provide fast, deterministic, scalable baseline extraction.
   - Layer 3 targets only hard cases where null_count > 3.
3. Selective LLM fallback (Gemini):
   - Used only for complex records to improve difficult fields while preserving deterministic outputs for easy cases.
   - Protected with rate limits and quota safeguards.

Why this design is strong:
- High throughput and interpretability from rules.
- Targeted quality uplift from LLM on ambiguous cases.
- Practical cost control by not sending all 10,000 records to the API.


## Layer-by-Layer Evaluation 

### Table 1: Layer Performance Summary

| Layer | Role | Key Outcome | Positive Assessment |
| --- | --- | --- | --- |
| Layer 1 | Rule-based extraction | Strong baseline parser on noisy prescriptions | Built a reliable foundation with robust normalization and abbreviation handling |
| Layer 2 | Scaled batch extraction | Around 87.5% baseline accuracy reported; strong field capture on major fields | Demonstrated that the rule-based approach is already high quality at scale |
| Layer 3 | Complex-case improvement (`null_count > 3`) | 442 complex cases identified (4.42%) and routed for improvement workflow | Smart selective strategy avoids unnecessary LLM usage and protects deterministic outputs |
| Layer 3 + Gemini (validated subset) | LLM-assisted enhancement for complex cases | 40 complex cases processed (quota-limited), 12 improved (30%), mostly in duration | Clear proof that targeted LLM fallback improves hard cases when quota is available |

### Table 2: Layer 2 Field-wise Capture

| Field | Captured | Null | % Complete |
| --- | ---: | ---: | ---: |
| medicine_name | 9,650 | 350 | 96.5% |
| strength | 9,814 | 186 | 98.1% |
| dosage | 6,211 | 3,789 | 62.1% |
| frequency | 8,690 | 1,310 | 86.9% |
| duration | 4,529 | 5,471 | 45.3% |
| notes | 3,485 | 6,515 | 34.9% |
| form | 6,064 | 3,936 | 60.6% |

Interpretation:
- Very strong extraction for medicine_name, strength, and frequency.
- Remaining gap is concentrated in duration, notes, and dosage, which are common hard fields in real prescriptions.

### Table 3: Gemini Improvement Evidence

| Metric | Rule-Based Only | With Gemini Enabled |
| --- | --- | --- |
| Complex cases considered | 442 | 40 processed (quota-limited) |
| Cases improved | 0 (0%) | 12 (30%) |
| Fields improved | 0 | 12 |
| Primary improvement area | Not applicable | Duration |
| Estimated improvement if all 442 processed | Not applicable | About 133 cases improved |





