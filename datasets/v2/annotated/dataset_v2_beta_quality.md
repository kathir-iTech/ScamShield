# V2 Dataset Quality Report (Beta)

**Date:** 2026-07-30 09:28:45

## Validation Summary

| Check | Result |
| ----- | ------ |
| Total Samples | 800 |
| Missing Field Issues | 2232 |
| Label Inconsistencies | 0 |
| Duplicates (text) | 0 removed |
| Duplicates (id) | 0 removed |
| Entities Extracted | 89/800 |
| Schema Compliance | Valid for 14 columns |

### Missing Fields

| Field | Missing Count |
| ----- | ------------: |
| extracted_entities | 558 |
| annotation_notes | 558 |
| created_at | 558 |
| updated_at | 558 |

✅ **All labels consistent** — no is_scam/ground_truth_label mismatch found.

## Synthetic Data Quality

- **Synthetic samples:** 242 (clearly identified via `source=synthetic`)
- **Manual samples:** 558
- **All realistic patterns** based on real-world Indian scam trends
- **Entity extraction** performed via regex for URLs, phones, UPI IDs, banks, emails, Aadhaar, PAN

## Annotation Consistency

| Aspect | Standard |
| ------ | -------- |
| Category naming | 25 standard categories from schema |
| Risk levels | CRITICAL/HIGH/MEDIUM/LOW/NONE |
| Language tags | en, ta-en, hi-en |
| Ground truth labels | scam / legitimate |
| Source tracking | synthetic, manual, cert-in, ncpc, rbi, etc. |
| Version | 2.0.0-beta |
