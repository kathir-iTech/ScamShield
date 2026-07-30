# Leakage Report: Gold Dataset vs Training Datasets

**Gold candidates:** 309
**Passed leakage check:** 308
**Leaked (removed):** 1

## Leakage Detection Methods

- **Exact match:** Direct string match against training texts
- **Cleaned exact:** Match after lowercasing/trimming
- **Near duplicate:** 4-gram overlap >= 85%
- **Template variant:** Entity-generalized text matches training template

## Leaked Candidates

| Category | Text | Source | Match Type |
|----------|------|--------|------------|
| INCOME_TAX_SCAM | Income Tax refund processing fee Rs 2,500 required to releas... | v2_beta | exact |
| INCOME_TAX_SCAM | Income Tax refund processing fee Rs 2,500 required to releas... | v2_gamma | exact |

## Summary

**Gold dataset is clean.** 308 samples passed all leakage checks.
Zero contamination from training datasets.
