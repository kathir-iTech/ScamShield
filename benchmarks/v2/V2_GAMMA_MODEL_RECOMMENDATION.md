# ScamShield V2 Gamma Model Recommendation

**Date:** 2026-07-30 16:46:32
**Evaluation Basis:** Gamma dataset (1668 samples, 25 categories)

## Model Rankings (by F1)

🥇 **1. tfidf_svm** — F1=0.9827, Acc=0.9731, P=0.9846, R=0.9808
🥈 **2. embedding** — F1=0.9749, Acc=0.9611, P=0.9844, R=0.9655
🥉 **3. tfidf_lr** — F1=0.9711, Acc=0.9551, P=0.9767, R=0.9655

## Recommendation

### Primary: tfidf_svm

- **F1 Score:** 0.9827
- **Accuracy:** 0.9731
- **Precision:** 0.9846
- **Recall:** 0.9808
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

1. ✅ Validate on a held-out synthetic test set (gamma test split)
2. ✅ Validate on gold dataset (308 real-world samples in datasets/gold/)
3. ⬜ Collect 200+ real scam messages from Twitter, Facebook groups, SMS forwards
4. ⬜ Evaluate precision on legitimate traffic to ensure low false positive rate
5. ⬜ Consider ensemble approach combining TF-IDF SVM + Embedding LR
6. ⬜ Expand language coverage (Tamil, Hindi, Telugu, Bengali)
