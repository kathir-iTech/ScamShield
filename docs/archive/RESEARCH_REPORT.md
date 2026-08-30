# Research Report — ScamShield v1.0.0

## Abstract

ScamShield presents a hybrid approach to SMS scam detection combining traditional machine learning with heuristic rule analysis. The system is designed specifically for the Indian telecommunications landscape, where scam patterns diverge significantly from global spam datasets.

## 1. Introduction

SMS-based fraud in India has grown exponentially with digital payment adoption. Common scams include fake KYC updates, UPI fraud, OTP phishing, and bank impersonation. Existing solutions either rely on blocklists (brittle) or general spam filters (not tuned for Indian patterns).

## 2. Methodology

### 2.1 Dataset
Training dataset combines the UCI SMS Spam Collection with augmented India-specific scam examples. The benchmark set includes 162 hand-labeled samples across 7 scam categories and legitimate messages.

### 2.2 Model Architecture
- **Vectorization**: TF-IDF with unigram + bigram features, max 5000 features, English stop word removal
- **Classifier**: LogisticRegression with L2 regularization (C=1.0), balanced class weights
- **Training**: 80/20 split, stratified by class

### 2.3 Rule Engine
18 heuristic patterns organized into categories:
- **Financial** (7 patterns): UPI references, OTP codes, bank names, payment requests, account alerts, credit card, GST
- **Urgency** (4 patterns): Time pressure, threats, action required, limited time
- **Phishing** (4 patterns): URL shorteners, suspicious domains, login requests, sensitive info requests
- **Identity** (3 patterns): KYC impersonation, government authority, courier/delivery

### 2.4 Confidence Scoring
Multi-factor aggregation combining:
- ML probability (weight: 0.40)
- Rule match score (weight: 0.25)
- Entity extraction (weight: 0.20)
- Explanation coherence (weight: 0.15)

## 3. Results

### 3.1 Overall Performance
- **Accuracy**: 83.3%
- **F1 Score**: 90.1%
- **ROC-AUC**: 0.91

### 3.2 Ablation
The hybrid approach (ML + Rules) outperforms either component alone. Rules catch region-specific scams (especially KYC and UPI fraud) that ML misses, while ML catches novel variants.

### 3.3 Error Analysis
- **False Positives** (22): Mostly promotional messages with urgency language ("Limited time offer!"). These are near-boundary cases where the system is correctly uncertain.
- **False Negatives** (5): Sophisticated scams mimicking legitimate communication patterns. Often short, simple messages without typical indicators.

## 4. Limitations

1. **Language**: Currently English-only; Indian multilingual scams (Hindi-English mix) may underperform
2. **Dataset Scale**: 162 benchmark samples; larger evaluation needed
3. **OCR Dependency**: Image analysis requires Tesseract 5.x, limiting deployment on minimal systems
4. **No Active Learning**: Model is static until retrained; no feedback loop yet
5. **URL Analysis**: Basic; does not fetch or sandbox URLs

## 5. Future Research

1. Multilingual NLP for Hindi, Tamil, Bengali, Hinglish code-mixed text
2. BERT-based fine-tuning for deeper semantic understanding
3. Active learning pipeline for continuous improvement
4. URL content analysis with headless browser sandboxing
5. Temporal pattern analysis (campaign detection across time)
6. Graph-based entity resolution for scam network discovery

## 6. Ethical Considerations

ScamShield is designed as a tool for individuals and organizations to protect against fraud. The system does not intercept messages without user consent, does not store message content beyond analysis, and provides transparent reasoning for all decisions.
