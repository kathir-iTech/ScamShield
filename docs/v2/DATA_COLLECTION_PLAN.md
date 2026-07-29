# ScamShield v2 – Data Collection Plan

## Objective

Collect **5,000–10,000 labelled Indian scam/legitimate messages** across 25 categories from reliable, publicly available sources. **No private user data will be scraped or collected.**

## Source Inventory

### 1. CERT-In Advisories (High Priority)

| Source | URL | Content | Access |
|--------|-----|---------|--------|
| CERT-In Alerts | https://www.cert-in.org.in/ | Weekly fraud alerts with sample scam messages | Public |
| CERT-In Twitter | @IndianCERT | Real-time scam warnings | Public |
| CERT-In PDF Archives | https://www.cert-in.org.in/PDF/ | Detailed fraud case studies | Public |

**Extraction method:** Download advisories, extract scam message templates and patterns mentioned in case studies.

### 2. RBI Fraud Alerts (High Priority)

| Source | URL | Content | Access |
|--------|-----|---------|--------|
| RBI Fraud Alerts | https://rbi.org.in/Scripts/BS_FraudAlerts.aspx | Bank fraud patterns, customer warnings | Public |
| RBI Press Releases | https://rbi.org.in/Scripts/BS_PressRelease.aspx | New scam modus operandi | Public |
| RBI CAFRAL | https://www.cafral.org.in/ | Fraud research reports | Public |

**Extraction method:** Parse fraud alert PDFs, extract scam descriptions and sample messages.

### 3. National Cyber Crime Reporting Portal (Medium Priority)

| Source | URL | Content | Access |
|--------|-----|---------|--------|
| NCRP | https://cybercrime.gov.in/ | Reported scam patterns (aggregated, no PII) | Public |
| Citizen Charter | https://cybercrime.gov.in/Webform/CitizenCharter.aspx | Scam awareness materials | Public |
| Awareness Resources | https://cybercrime.gov.in/Webform/Awareness.aspx | Educational content with scam examples | Public |

**Note:** Do NOT scrape individual complaints. Use only published awareness resources and aggregated statistics.

### 4. NPCI Circulars (Medium Priority)

| Source | URL | Content | Access |
|--------|-----|---------|--------|
| NPCI Fraud Updates | https://www.npci.org.in/ | UPI fraud patterns, new fraud vectors | Public |
| NPCI Press Releases | https://www.npci.org.in/media/press-releases | UPI safety advisories | Public |

### 5. Government Scam Awareness Pages (High Priority)

| Source | URL | Content |
|--------|-----|---------|
| PIB Fact Check | https://factcheck.pib.gov.in/ | Government scheme scam debunks |
| DoT Sanchar Saathi | https://sancharsaathi.gov.in/ | Telecom scam awareness |
| MeitY Cyber Awareness | https://www.meity.gov.in/cyber-awareness | Cyber fraud educational content |
| I4C (Indian Cyber Crime Coordination Centre) | https://i4c.gov.in/ | Cyber fraud patterns and alerts |

### 6. Telecom Provider Fraud Pages (Medium Priority)

| Source | URL | Content |
|--------|-----|---------|
| TRAI | https://www.trai.gov.in/ | Telecom scam advisories |
| Vodafone Idea Safety | https://www.myvi.in/safety | Telecom fraud examples |
| Airtel Safety | https://www.airtel.in/safety-tips | Scam SMS examples |
| Jio Cyber Safety | https://www.jio.com/cyber-safety | Fraud awareness |

### 7. Bank Fraud Awareness Pages (Medium Priority)

| Source | URL | Content |
|--------|-----|---------|
| SBI Safe Banking | https://bank.sbi/web/security | Bank fraud examples |
| HDFC Security | https://www.hdfcbank.com/personal/safe-banking | Phishing examples |
| ICICI Safety | https://www.icicibank.com/safety | Fraud message examples |
| Axis Security | https://www.axisbank.com/security-centre | KYC scam examples |
| IBA (Indian Banks' Association) | https://www.iba.org.in/ | Industry fraud patterns |

### 8. Public Phishing Repositories (Medium Priority)

| Source | URL | Content |
|--------|-----|---------|
| PhishTank | https://phishtank.org/ | Phishing URLs (scam messages referencing these) |
| OpenPhish | https://openphish.com/ | Active phishing URLs |
| URLHaus | https://urlhaus.abuse.ch/ | Malicious URLs |
| APWG | https://apwg.org/ | Phishing attack trends and examples |

### 9. Academic and Public Datasets (Medium Priority)

| Source | Description | Relevance |
|--------|-------------|-----------|
| UCI SMS Spam Collection | 5,574 SMS (v1 training data) | Low — UK-centric but useful for augmentation |
| NUS SMS Corpus | ~50,000 SMS | Low — general language, not scam-specific |
| Indian Language SMS Datasets | Various academic datasets | Medium — language diversity |
| Kaggle SMS Spam Collections | Multiple community datasets | Low-Medium — need Indian-specific filtering |

### 10. Synthetic Template Generation (Fallback, ≤20% per category)

Create templates from real scam patterns found in sources 1–7:

```
[Bank] Alert: Your [account/card] has been [blocked/suspended/deactivated].
Click [URL] to [update/verify/restore] your [KYC/account/details].
```

Generate variations by substituting:
- Bank names: SBI, HDFC, ICICI, Axis, PNB, Kotak, Yes Bank, etc.
- Action verbs: blocked, suspended, deactivated, frozen, restricted
- Urgency phrases: immediately, within 24 hours, today only
- URLs: Use placeholder `[URL]` for model training

## Collection Procedure

### Phase 1: Source Harvesting (Weeks 1-2)
1. Download all advisory PDFs from CERT-In, RBI, NPCI
2. Extract scam message examples from awareness pages
3. Parse government fact-check debunks for scam references
4. Collect URLs from phishing repositories

### Phase 2: Template Extraction (Weeks 3-4)
1. Extract message templates from advisories
2. Convert case studies into structured samples
3. Generate synthetic variants (max 20% of category)
4. Cross-reference with existing v1 dataset for relevant Indian samples

### Phase 3: Annotation (Weeks 5-8)
1. Apply annotation guidelines (see ANNOTATION_GUIDE.md)
2. Double-annotate 10% random sample (κ ≥ 0.90)
3. Balance categories to ≥ 100 samples each
4. Review and adjudicate disagreements

### Phase 4: Quality Review (Week 9)
1. Deduplication check
2. Schema validation
3. Coverage gap analysis
4. Release v2.0.0-alpha

## Data Handling

- **License**: Each source's terms must be respected. Government advisories are generally public domain. Public datasets have varying licenses — document each.
- **PII**: No actual PII will be collected. All samples from advisories are already anonymized. Synthetic data uses placeholders.
- **Attribution**: Each sample's `source` field records origin for traceability.

## Tools

| Tool | Purpose |
|------|---------|
| Python `requests` + `BeautifulSoup` | Web scraping of advisory pages |
| `pdfplumber` / `PyMuPDF` | PDF text extraction |
| `spaCy` + `regex` | Entity extraction |
| Custom `build_dataset.py` | Assemble raw → annotated pipeline |
| Custom `validate.py` | Schema validation |

## Data Collection Checklist

- [ ] CERT-In advisories (last 3 years) downloaded and parsed
- [ ] RBI fraud alerts scraped and categorized
- [ ] NPCI circulars extracted for UPI patterns
- [ ] Government scam awareness pages processed
- [ ] Bank security pages reviewed for examples
- [ ] Telecom provider fraud pages extracted
- [ ] Public phishing repositories filtered for Indian-relevant
- [ ] Academic datasets reviewed for usable samples
- [ ] Synthetic templates generated (≤20% cap)
- [ ] All sources documented with attribution
- [ ] No PII in dataset
- [ ] Balanced distribution across categories