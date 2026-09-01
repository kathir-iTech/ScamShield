"""
Export ScamShield's trained LogisticRegression model and TfidfVectorizer
to browser-ready JavaScript artifacts.

m2cgen can't handle 5000 features (recursion overflow), so we extract
the raw weights directly and write a hand-rolled scoring function.
Logistic regression scoring is trivially: sigmoid(x . coef + intercept).

Produces:
  1. model.js       — classifier weights, intercept, and predict function
  2. vectorizer.js  — TF-IDF vectorizer (vocab, IDF, stop words, transform)
"""

import json
import os
import sys
import joblib
import numpy as np

BACKEND_DIR = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.insert(0, BACKEND_DIR)

MODEL_PATH = os.path.join(BACKEND_DIR, "models", "model.joblib")
VECTORIZER_PATH = os.path.join(BACKEND_DIR, "models", "vectorizer.joblib")
OUTPUT_MODEL = os.path.join(os.path.dirname(__file__), "model.js")
OUTPUT_VECTORIZER = os.path.join(os.path.dirname(__file__), "vectorizer.js")

# ── 1. Load artifacts ───────────────────────────────────────────────
print("Loading model and vectorizer...")
model = joblib.load(MODEL_PATH)
vectorizer = joblib.load(VECTORIZER_PATH)

print("  Model type:", type(model).__name__)
print("  Coef shape:", model.coef_.shape)
print("  Intercept:", model.intercept_)
print("  Classes:", model.classes_)
print("  Vocab size:", len(vectorizer.vocabulary_))
print("  IDF length:", len(vectorizer.idf_))

# ── 2. Extract model weights ────────────────────────────────────────
coef = model.coef_[0].tolist()
intercept = float(model.intercept_[0])

print("\nModel weights:", len(coef), "coefficients, intercept=", round(intercept, 6))

# ── 3. Export model.js ──────────────────────────────────────────────
print("Writing model.js...")

coef_json = json.dumps(coef)

MODEL_JS = """// Auto-generated from ScamShield's LogisticRegression model
// Pure JavaScript - no dependencies. Uses sigmoid(coef . features + intercept).

var MODEL_COEF = """ + coef_json + """;
var MODEL_INTERCEPT = """ + str(intercept) + """;

/**
 * Score a feature vector through the logistic regression.
 * @param {number[]} features - TF-IDF feature vector (length = vocab_size)
 * @returns {Object} { score, label, confidence }
 */
function predict(features) {
  var dot = MODEL_INTERCEPT;
  for (var i = 0; i < MODEL_COEF.length; i++) {
    dot += MODEL_COEF[i] * (features[i] || 0);
  }
  var probScam = 1 / (1 + Math.exp(-dot));
  var probSafe = 1 - probScam;
  var label = probScam >= 0.5 ? 'scam' : 'safe';
  var confidence = Math.max(probSafe, probScam);
  return { score: probScam, label: label, confidence: confidence };
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { predict: predict, MODEL_COEF: MODEL_COEF, MODEL_INTERCEPT: MODEL_INTERCEPT };
}
"""

with open(OUTPUT_MODEL, "w", encoding="utf-8") as f:
    f.write(MODEL_JS)

print("  Written to", OUTPUT_MODEL, "(", os.path.getsize(OUTPUT_MODEL), "bytes)")

# ── 4. Export vectorizer.js ─────────────────────────────────────────
print("Writing vectorizer.js...")

vocab = {k: int(v) for k, v in vectorizer.vocabulary_.items()}
idf = vectorizer.idf_.tolist()
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
# The pickled vectorizer stores stop_words='english' (the param string), not the fitted set.
# Use sklearn's canonical English stop words list to match what transform() uses internally.
stop_words = sorted(ENGLISH_STOP_WORDS)

vocab_json = json.dumps(vocab, ensure_ascii=False)
idf_json = json.dumps(idf)
stop_words_json = json.dumps(sorted(stop_words))

# Build the JS string carefully — no f-strings with braces
ngram_range_str = str(vectorizer.ngram_range)
max_features_val = vectorizer.max_features
min_df_val = vectorizer.min_df
max_df_val = vectorizer.max_df

VECTORIZER_JS = """// Auto-generated from ScamShield's TfidfVectorizer
// Pure JavaScript - tokenizes text, computes TF-IDF, L2-normalizes.
// Config: ngram_range=""" + ngram_range_str + """, max_features=""" + str(max_features_val) + """, min_df=""" + str(min_df_val) + """, max_df=""" + str(max_df_val) + """

var VOCAB = """ + vocab_json + """;
var IDF = """ + idf_json + """;
var STOP_WORDS = new Set(""" + stop_words_json + """);
var VOCAB_SIZE = """ + str(len(vocab)) + """;

var TOKEN_RE = /[a-z0-9_]{2,}/g;

var URL_RE = /https?:\\/\\/(?:[-\\w.]|[\\da-fA-F]{2})+(?:\\/[^\\s]*)?/gi;
var EMAIL_RE = /[a-z0-9._%+-]+@[a-z0-9.-]+\\.[a-z]{2,}\\b/gi;
var PHONE_RE = /(?:\\+?\\d{1,3}[-.\\s]?)?\\(?\\d{3}\\)?[-.\\s]?\\d{3}[-.\\s]?\\d{4}\\b/g;
var UPI_RE = /[a-z0-9._-]+@[a-z]{3,}\\b/gi;
var VALID_UPI = new Set(['paytm','gpay','phonepe','amazonpay','bhim','upi','ybl','ibl','apl','axl','payu','icici','hdfc','sbi','kotak']);

function cleanText(text) {
  var placeholders = {};
  var idx = 0;
  text = text.replace(URL_RE, function(m) { var key = '__url_' + idx + '__'; placeholders[key] = m; idx++; return key; });
  text = text.replace(EMAIL_RE, function(m) { var key = '__email_' + idx + '__'; placeholders[key] = m; idx++; return key; });
  text = text.replace(PHONE_RE, function(m) { var key = '__phone_' + idx + '__'; placeholders[key] = m; idx++; return key; });
  text = text.replace(UPI_RE, function(m) {
    var h = m.split('@')[1] ? m.split('@')[1].toLowerCase() : '';
    if (VALID_UPI.has(h)) { var key = '__upi_' + idx + '__'; placeholders[key] = m; idx++; return key; }
    return m;
  });
  text = text.toLowerCase().replace(/[^a-z0-9\\s_]/g, '').replace(/\\s+/g, ' ').trim();
  var keys = Object.keys(placeholders);
  for (var i = 0; i < keys.length; i++) { text = text.replace(keys[i], placeholders[keys[i]]); }
  return text;
}

function tokenize(text) {
  var matches = text.match(TOKEN_RE);
  if (!matches) return [];
  var unigrams = [];
  for (var i = 0; i < matches.length; i++) {
    if (!STOP_WORDS.has(matches[i])) {
      unigrams.push(matches[i]);
    }
  }
  var bigrams = [];
  for (var i = 0; i < matches.length - 1; i++) {
    bigrams.push(matches[i] + ' ' + matches[i + 1]);
  }
  return unigrams.concat(bigrams);
}

function transform(text) {
  var cleaned = cleanText(text);
  var tokens = tokenize(cleaned);
  var tf = {};
  for (var i = 0; i < tokens.length; i++) {
    var t = tokens[i];
    tf[t] = (tf[t] || 0) + 1;
  }
  var vector = new Array(VOCAB_SIZE);
  for (var i = 0; i < VOCAB_SIZE; i++) vector[i] = 0;
  var entries = Object.entries(tf);
  for (var i = 0; i < entries.length; i++) {
    var term = entries[i][0];
    var count = entries[i][1];
    var idx = VOCAB[term];
    if (idx !== undefined) {
      vector[idx] = count * IDF[idx];
    }
  }
  var norm = 0;
  for (var i = 0; i < VOCAB_SIZE; i++) {
    norm += vector[i] * vector[i];
  }
  norm = Math.sqrt(norm);
  if (norm > 0) {
    for (var i = 0; i < VOCAB_SIZE; i++) {
      vector[i] /= norm;
    }
  }
  return vector;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { transform: transform, cleanText: cleanText, tokenize: tokenize, VOCAB: VOCAB, IDF: IDF, STOP_WORDS: STOP_WORDS, VOCAB_SIZE: VOCAB_SIZE };
}
"""

with open(OUTPUT_VECTORIZER, "w", encoding="utf-8") as f:
    f.write(VECTORIZER_JS)

print("  Written to", OUTPUT_VECTORIZER, "(", os.path.getsize(OUTPUT_VECTORIZER), "bytes)")

# ── 5. Quick validation ─────────────────────────────────────────────
print("\nVectorizer config confirmation:")
print("  sublinear_tf:", getattr(vectorizer, 'sublinear_tf', False))
print("  norm:", getattr(vectorizer, 'norm', 'l2'))
print("  smooth_idf:", getattr(vectorizer, 'smooth_idf', True))

print("\nExport complete.")
