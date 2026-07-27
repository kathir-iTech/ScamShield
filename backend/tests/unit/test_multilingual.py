from core.multilingual import (
    detect_language,
    normalize_tanglish,
    normalize_hindi_english,
    normalize_unicode,
    preprocess_multilingual,
    TANGLISH_NORM_MAP,
    HINDI_NORM_MAP,
)


def test_detect_language_english():
    assert detect_language("Hello, how are you?") == "en"
    assert detect_language("This is a test message with no Tamil") == "en"


def test_detect_language_tamil():
    result = detect_language("உங்கள் SBI கணக்கு KYC புதுப்பிக்கவும்")
    assert result == "ta"


def test_detect_language_tanglish():
    assert detect_language("Unga account block aagum") == "tangling"
    assert detect_language("Eppadi irukinga") == "tangling"
    assert detect_language("Neraya cashback") == "tangling"


def test_detect_language_hindi_english():
    assert detect_language("Aapka account block ho gaya hai") == "hi-en"
    assert detect_language("Yeh sarkari yojna hai") == "hi-en"


def test_normalize_tanglish_unga():
    assert "your" in normalize_tanglish("unga account")


def test_normalize_tanglish_pannunga():
    assert "please do" in normalize_tanglish("pannunga")


def test_normalize_tanglish_multiple():
    result = normalize_tanglish("neenga romba nalla irukinga")
    assert "good" in result or "very" in result


def test_normalize_tanglish_identity():
    assert normalize_tanglish("hello world") == "hello world"


def test_normalize_hindi_english():
    result = normalize_hindi_english("aap sarkari yojna")
    assert "you" in result
    assert "government" in result
    assert "scheme" in result


def test_normalize_hindi_english_identity():
    assert normalize_hindi_english("hello world") == "hello world"


def test_normalize_unicode():
    text = "Hello\u200cWorld"
    result = normalize_unicode(text)
    assert "\u200c" not in result


def test_normalize_unicode_multiple_spaces():
    result = normalize_unicode("Hello   World")
    assert "  " not in result


def test_preprocess_multilingual_english():
    processed, lang = preprocess_multilingual("Hello world")
    assert lang == "en"


def test_preprocess_multilingual_tanglish():
    processed, lang = preprocess_multilingual("Unga account block aagum")
    assert lang == "tangling"
    assert "your" in processed


def test_preprocess_multilingual_hindi():
    processed, lang = preprocess_multilingual("Aap sarkari yojna karein")
    assert lang == "hi-en"
    assert "you" in processed
    assert "government" in processed
    assert "scheme" in processed


def test_preprocess_multilingual_unicode():
    processed, lang = preprocess_multilingual("Hello\u200cWorld")
    assert "\u200c" not in processed


def test_tanglish_norm_map_has_key():
    assert "unga" in TANGLISH_NORM_MAP
    assert "pannunga" in TANGLISH_NORM_MAP
    assert "irukku" in TANGLISH_NORM_MAP
    assert "nalla" in TANGLISH_NORM_MAP
    assert "romba" in TANGLISH_NORM_MAP


def test_hindi_norm_map_has_key():
    assert "aap" in HINDI_NORM_MAP
    assert "sarkari" in HINDI_NORM_MAP
    assert "yojna" in HINDI_NORM_MAP
    assert "karein" in HINDI_NORM_MAP
