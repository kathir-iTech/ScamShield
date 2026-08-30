# REPORT 7: DATA QUALITY

## 1. Training Dataset (scam_dataset.csv)

| Metric | Value |
|---|---|
| Total samples | 5,312 |
| Scam samples | 3,782 (71.2%) |
| Safe samples | 1,530 (28.8%) |
| Features | Message text + label |
| Label balance | Imbalanced (2.5:1 scam:safe) |
| Language coverage | English only |
| India-specific coverage | Partial (some UPI/KYC patterns) |

**Quality issues:**
1. **Class imbalance** — Model may over-predict "scam". Precision on safe messages may be poor.
2. **Single language** — Only English. Hindi, Tamil, Telugu, Bengali not represented despite being target use case.
3. **Label noise** — No confidence score on labels; no multi-annotator validation.
4. **Temporal bias** — All data from a single point in time; doesn't reflect evolving scam tactics.
5. **Source bias** — Dataset origin not documented. May over-represent certain scam types.
6. **Duplicate detection** — Not checked for near-duplicate messages.

## 2. Knowledge Base Quality

### Patterns (`knowledge/patterns/`)
| File | Status | Issues |
|---|---|---|
| `otp_patterns.json` | ✅ Populated | 4 patterns (banking, SIM swap, wallet, phishing) |
| `upi_patterns.json` | ✅ Populated | 5 patterns |
| `kyc_patterns.json` | ✅ Populated | 3 patterns |
| `payment_patterns.json` | ⚠️ Partial | Has entries but incomplete |
| `urgency_patterns.json` | ⚠️ Partial | Only 2 patterns |
| `job_patterns.json` | ❌ Empty | `[]` |
| `lottery_patterns.json` | ❌ Empty | `[]` |
| `investment_patterns.json` | ❌ Empty | `[]` |
| `impersonation_patterns.json` | ❌ Empty | `[]` |
| `delivery_patterns.json` | ❌ Empty | `[]` |
| `loan_patterns.json` | ❌ Empty | `[]` |

### Watchlists (`knowledge/watchlists/`)
| File | Status |
|---|---|
| `known_domains.json` | ⚠️ Partial (6 entries) |
| `known_emails.json` | ❌ Empty (`[]`) |
| `known_phones.json` | ❌ Empty (`[]`) |
| `known_upi.json` | ⚠️ Partial (15 entries including test/vdemo IDs) |

### Advisories (`knowledge/advisories/`)
| File | Status |
|---|---|
| `rbi_advisories.json` | ✅ Populated (12 advisories, 2021-2024) |
| `cert_in_advisories.json` | ✅ Populated (10 advisories) |
| `npci_advisories.json` | ✅ Populated (5 advisories) |
| `bank_advisories.json` | ✅ Populated (10 advisories from 4 banks) |

**Issues:**
1. **6 of 12 pattern files are empty** — reduces knowledge matching effectiveness
2. **Watchlists are minimal** — 6 domains, 15 UPI IDs — likely ineffective for real-world matching
3. **Advisory dates are fictional** — No source URLs or verification. May mislead users into thinking these are official advisories.
4. **No freshness** — No mechanism to update knowledge base data
5. **Format inconsistency** — Some files use `"description"` vs `"details"` for pattern metadata

## 3. Evaluation Dataset

**Status:** Framework exists (`evaluation/` directory with `evaluate_pipeline.py`), but dataset directories are empty:

```
evaluation/dataset/banking/       ❌ Empty
evaluation/dataset/crypto/        ❌ Empty
evaluation/dataset/delivery/      ❌ Empty
evaluation/dataset/government/    ❌ Empty
evaluation/dataset/loan/          ❌ Empty
evaluation/dataset/lottery/       ❌ Empty
```

**Impact:** Cannot benchmark, cannot detect regressions, cannot validate improvements.

## 4. ML Model Quality

| Metric | Value | Assessment |
|---|---|---|
| Accuracy | ~83% | Reasonable baseline |
| Precision | Unknown (not computed) | |
| Recall | Unknown (not computed) | |
| F1 Score | Unknown (not computed) | |
| AUC-ROC | Unknown (not computed) | |
| Confusion Matrix | Unknown (not computed) | |

**Issues:**
1. No formal evaluation metrics published
2. No train/test split information
3. No cross-validation results
4. Model.joblib is a binary blob — no version, no provenance, no reproducibility
5. `train.py` script exists but training process is not automated or documented
6. Model calibration infrastructure exists (`core/calibration/`) but is not wired to the ML step

## 5. Configuration Data

| Config Source | Format | Quality |
|---|---|---|
| `.env.example` | Key-value | Good — documents all variables |
| `docker-compose.yml` | YAML | Good — well-structured |
| `k8s/configmap.yaml` | YAML | Good — mirrors env vars |
| `core/config/*.py` | Pydantic | Excellent — validated at startup |

**Issues:**
1. `.env.example` lists API keys that don't correspond to implemented connectors
2. Some config values have no defaults and will fail silently if unset
3. No config versioning — can't track changes over time

## 6. Data Governance

| Practice | Status |
|---|---|
| Data classification | ❌ Not defined |
| Data retention policy | ❌ Not defined |
| Data anonymization | ✅ PII masking present |
| Data deletion support | ❌ No data stored |
| Data backup | ❌ Not applicable (no persistence) |
| Data provenance tracking | ❌ Analysis results include model version but no dataset version |
| Privacy impact assessment | ❌ Not performed |
| User data handling notice | ❌ Not provided |
