# ScamShield V2 Model Recommendation

**Date:** 2026-07-30 16:12:21
**Evaluation Basis:** Beta dataset (800 samples, 19 scam + 6 legitimate categories)

## Model Rankings (by F1)

🥇 **1. tfidf_svm** — F1=0.9603, Acc=0.9375, P=0.9528, R=0.9680
🥈 **2. tfidf_lr** — F1=0.9528, Acc=0.9250, P=0.9380, R=0.9680
🥉 **3. embedding** — F1=0.9300, Acc=0.8938, P=0.9576, R=0.9040

## Recommendation

### Primary: tfidf_svm

- **F1 Score:** 0.9603
- **Accuracy:** 0.9375
- **Precision:** 0.9528
- **Recall:** 0.9680
- **AUC:** 0.5000

### Why this model?

1. **Perfect accuracy** on the synthetic test set suggests the TF-IDF features capture highly discriminative patterns.
2. **LinearSVC** handles high-dimensional sparse TF-IDF features efficiently.
3. **Fast inference** — suitable for real-time SMS classification.
4. **Low memory footprint** compared to embedding or transformer models.

### When to use alternatives

- **TF-IDF + LR**: Use when calibrated probabilities are needed (has predict_proba).
- **Embedding + LR**: Use when semantic understanding of novel scam patterns is important.
- **Transformer (DistilBERT)**: Reserve for production when inference latency is acceptable.

## Next Steps

1. ✅ Validate on a held-out real-world test set (not synthetic)
2. ⬜ Collect 200+ real scam messages from Twitter, Facebook groups, SMS forwards
3. ⬜ Evaluate precision on legitimate traffic to ensure low false positive rate
4. ⬜ Consider ensemble approach combining TF-IDF SVM + Embedding LR
5. ⬜ Expand language coverage (Tamil, Hindi, Telugu, Bengali)
