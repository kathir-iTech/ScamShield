# Multilingual Engine

## Language Detection

`core/multilingual.py` detects four language categories:

| Language | Detection Method |
|----------|-----------------|
| `en` | No Tamil/Hindi/Tanglish patterns detected |
| `ta` | Tamil Unicode characters (> 3 or > 10% of text) |
| `tangling` | Tanglish normalization map matches |
| `hi-en` | Hindi-English normalization map matches |

## Tanglish Normalization

Maps common Tanglish words to English equivalents:

- "unga/ungal" → "your"
- "pannu/panni/pannunga" → "do/done/please do"
- "irukku/aagum" → contextual mapping
- 70+ Tanglish word mappings

## Hindi-English Normalization

Maps common Hinglish words:

- "aap" → "you", "sarkari" → "government"
- 30+ Hinglish word mappings

## Preprocessing Pipeline

1. Unicode normalization (NFKC)
2. Zero-width character removal
3. Language detection
4. Language-specific normalization
5. Standard text cleaning

## Usage

```python
from core.multilingual import preprocess_multilingual, detect_language

processed, lang = preprocess_multilingual("Unga account block aagum")
assert lang == "tangling"
assert "your" in processed
```

## Expanding Language Support

To add a new language:

1. Add normalization mappings dict
2. Add detection logic to `detect_language()`
3. Add normalization function
4. Wire into `preprocess_multilingual()`
