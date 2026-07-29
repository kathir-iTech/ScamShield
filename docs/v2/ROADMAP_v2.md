# ScamShield v2 – Production Roadmap

## Current State (v1.1)

- Model: TF-IDF + Logistic Regression (UCI SMS Spam 2005–2012, UK-centric)
- Benchmark accuracy: 82.1% (52% FP rate on legitimate, 0% recall on romance scam)
- Dataset: 5,715 rows (888 scam, 4,827 safe) — only 12–15 samples per Indian category
- Rules: 14 FP + 9 FN refinement rules, OTP detection in 7 locations
- Auth: Custom JWT with no-op revocation
- Frontend: 5 unused components, TypeScript strict mode off

## Vision (v2.0 Production)

- Model: TF-IDF + Logistic Regression trained on 5000+ Indian scam messages
- Benchmark accuracy: ≥ 92%, FPR ≤ 5%, FNR ≤ 10%
- Dataset: 25 categories, ≥ 100 samples each
- All v1.0 critical blockers resolved

## Roadmap

### Phase 1: Data Foundation (Q3 2026) ← YOU ARE HERE

**Goal:** Build the 5000–10000 labelled Indian scam dataset

| Task | Duration | Dependencies | Owner |
|------|----------|--------------|-------|
| 1.1 Source harvesting (CERT-In, RBI, NPCI, NCPC) | 2 weeks | None | Data Team |
| 1.2 Template extraction and synthetic generation | 2 weeks | 1.1 | Data Team |
| 1.3 Annotation (batch 1: 1000 samples) | 2 weeks | 1.2 | Annotation Team |
| 1.4 Quality review and deduplication | 1 week | 1.3 | QA Team |
| 1.5 Release v2.0.0-alpha (1000+ samples) | — | 1.4 | — |

**Deliverable:** `datasets/v2/annotated/v2.0.0-alpha/`

### Phase 2: Evaluation Framework (Q3 2026)

**Goal:** Build the benchmark and evaluation pipeline

| Task | Duration | Dependencies | Owner |
|------|----------|--------------|-------|
| 2.1 Benchmark dataset (100+ curated samples) | 1 week | 1.2 | ML Team |
| 2.2 Evaluation scripts (metrics, error analysis) | 1 week | None | ML Team |
| 2.3 Model comparison pipeline | 1 week | 2.2 | ML Team |
| 2.4 Baseline evaluation on v1 model | 0.5 week | 2.3 | ML Team |

**Deliverable:** `benchmarks/v2/` framework + baseline metrics

### Phase 3: Model Training (Q4 2026)

**Goal:** Train and select the best model for production

| Task | Duration | Dependencies | Owner |
|------|----------|--------------|-------|
| 3.1 Train TF-IDF + LR on v2 alpha dataset | 1 week | 1.5, 2.3 | ML Team |
| 3.2 Train TF-IDF + SVM on v2 alpha dataset | 1 week | 1.5, 2.3 | ML Team |
| 3.3 Train Embedding + LR on v2 alpha dataset | 1 week | 1.5, 2.3 | ML Team |
| 3.4 Train DistilBERT (if dataset ≥ 3000) | 2 weeks | 1.5, 2.3 | ML Team |
| 3.5 Cross-validation and hyperparameter tuning | 1 week | 3.1–3.4 | ML Team |
| 3.6 Model selection and threshold optimization | 0.5 week | 3.5 | ML Team |

**Deliverable:** Selected model with optimal thresholds and per-category metrics

### Phase 4: Dataset Expansion (Q4 2026 – Q1 2027)

**Goal:** Scale dataset to 5000+ samples

| Task | Duration | Dependencies | Owner |
|------|----------|--------------|-------|
| 4.1 Annotation (batch 2: 2000 samples) | 3 weeks | 1.4 | Annotation Team |
| 4.2 Hard case collection (romance, digital arrest) | 2 weeks | 1.1 | Data Team |
| 4.3 Language diversity (Hinglish, Tanglish, Tamil) | 2 weeks | 4.2 | Data Team |
| 4.4 Release v2.0.0-beta (3000+ samples) | — | 4.1–4.3 | — |

**Deliverable:** `datasets/v2/annotated/v2.0.0-beta/`

### Phase 5: Model v2 Training (Q1 2027)

**Goal:** Train production model on full dataset

| Task | Duration | Dependencies | Owner |
|------|----------|--------------|-------|
| 5.1 Retrain selected model on v2 beta dataset | 1 week | 4.4 | ML Team |
| 5.2 Evaluate on benchmark, iterate | 2 weeks | 5.1, 2.1 | ML Team |
| 5.3 Category-aware threshold calibration | 1 week | 5.2 | ML Team |
| 5.4 Adversarial testing (edge cases, obfuscation) | 1 week | 5.3 | QA Team |

**Deliverable:** Production-ready model with benchmark report

### Phase 6: Rule Engine Cleanup (Q1 2027)

**Goal:** Consolidate and simplify rule engine

| Task | Duration | Dependencies | Owner |
|------|----------|--------------|-------|
| 6.1 Audit existing 23 refinement rules | 1 week | None | Engineering |
| 6.2 Consolidate OTP detection (7 locations → 1) | 1 week | 6.1 | Engineering |
| 6.3 Remove redundant/conflicting rules | 1 week | 6.1 | Engineering |
| 6.4 Integrate model + rule engine scores | 2 weeks | 5.3, 6.3 | Engineering |

**Deliverable:** Clean rule engine with OTP detection in one place

### Phase 7: Production Hardening (Q1–Q2 2027)

**Goal:** Fix all v1.0 critical blockers

| Task | Duration | Dependencies | Owner |
|------|----------|--------------|-------|
| 7.1 Replace custom JWT with pyjwt | 2 weeks | None | Engineering |
| 7.2 Add proper token revocation (Redis) | 1 week | 7.1 | Engineering |
| 7.3 Enable TypeScript strict mode | 1 week | None | Frontend |
| 7.4 Remove dead frontend components (5) | 1 week | 7.3 | Frontend |
| 7.5 Remove dead middleware (RateLimitMiddleware) | 0.5 week | None | Engineering |
| 7.6 Deduplicate bank lists (4+ files → 1) | 0.5 week | None | Engineering |
| 7.7 Security audit and penetration testing | 2 weeks | 7.1–7.6 | Security |

**Deliverable:** Production-hardened backend and frontend

### Phase 8: Release v2.0 (Q2 2027)

**Goal:** Production release

| Task | Duration | Dependencies | Owner |
|------|----------|--------------|-------|
| 8.1 Final evaluation on v2 benchmark | 1 week | 5.3, 7.7 | ML Team |
| 8.2 Regression check vs v1.1 | 0.5 week | 8.1 | ML Team |
| 8.3 Performance testing (load test, latency SLO) | 1 week | 7.7 | Engineering |
| 8.4 Documentation update | 1 week | 8.1–8.3 | Docs Team |
| 8.5 Release v2.0 | — | 8.4 | — |

**Deliverable:** ScamShield v2.0 production release

## Timeline (Gantt)

```
Q3 2026          Q4 2026          Q1 2027          Q2 2027
│                │                │                │
Phase 1 ████████ │                │                │
Phase 2    ████████               │                │
Phase 3         ████████          │                │
Phase 4              ██████████████                │
Phase 5                   ████████████             │
Phase 6                        ████████            │
Phase 7                             ██████████████  │
Phase 8                                  ████████████
```

## Critical Path

The critical path to production is:
1. **Dataset collection** (Phase 1) → no substitute, must be done first
2. **Model training** (Phase 3) → dependent on Phase 1
3. **Production hardening** (Phase 7) → can start in parallel with Phase 3

Parallel workstreams:
- Evaluation framework (Phase 2): independent, start immediately
- Rule engine cleanup (Phase 6): independent, can start now
- Auth replacement (7.1): independent, start immediately
- Frontend fixes (7.3–7.4): independent, start immediately

## Risks and Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Difficulty collecting 100+ romance scam samples | High | Medium | Proactively source from CERT-In case studies, awareness materials, and synthetic generation |
| Low annotator agreement on hard categories | Medium | Medium | Clear annotation guide, regular calibration sessions |
| Embedding/Transformer models don't outperform TF-IDF | Low | Medium | TF-IDF + LR is already good enough (88–92% F1); keep as production model |
| Dataset quality issues | High | Low | Automated validation, double annotation, regular audits |
| Timeline slippage | Medium | Low | Parallel workstreams, weekly milestone tracking |
| New scam categories emerge | Medium | High | Versioned dataset with update mechanism; model retraining quarterly |

## Decision Gates

| Gate | Criteria | Go | No-Go |
|------|----------|-----|-------|
| G1: Dataset v2.0.0-alpha | ≥1000 samples, ≥20 categories, κ≥0.80 | Proceed to Phase 3 | Expand annotation effort |
| G2: Model selection | Best model achieves ≥88% F1 on benchmark | Proceed to Phase 5 | Re-evaluate model architecture |
| G3: Production readiness | Auth replaced, strict mode on, benchmarks ≥92% | Release v2.0 | Address blockers |

## Resource Plan

| Role | Phase 1 | Phase 2 | Phase 3 | Phase 4 | Phase 5 | Phase 6 | Phase 7 | Phase 8 |
|------|---------|---------|---------|---------|---------|---------|---------|---------|
| Data Engineer | 1 | — | — | 1 | — | — | — | — |
| ML Engineer | — | 1 | 1 | — | 1 | 1 | — | 1 |
| Annotator | 2 | — | — | 3 | — | — | — | — |
| Backend Engineer | — | — | — | — | — | 1 | 2 | 1 |
| Frontend Engineer | — | — | — | — | — | — | 1 | — |
| QA | 0.5 | 0.5 | 0.5 | 0.5 | 1 | 0.5 | 1 | 1 |
| Security | — | — | — | — | — | — | 1 | — |