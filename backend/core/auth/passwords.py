from __future__ import annotations

PASSWORD_MIN_LENGTH: int = 10

_COMMON_PASSWORDS = frozenset(
    {
        "1234567890",
        "12345678901",
        "abc123456789",
        "admin123456",
        "dragon12345",
        "iloveyou123",
        "letmein1234",
        "monkey12345",
        "password123",
        "password1234",
        "passw0rd123",
        "qwerty12345",
        "welcome1234",
    }
)


def _bcrypt():
    try:
        import bcrypt
    except ImportError as exc:  # pragma: no cover - dependency declared in requirements
        raise RuntimeError(
            "bcrypt is required for password hashing but is not installed"
        ) from exc
    return bcrypt


def _min_length() -> int:
    try:
        from config import settings

        return int(getattr(settings, "PASSWORD_MIN_LENGTH", PASSWORD_MIN_LENGTH))
    except Exception:  # pragma: no cover - settings unavailable in isolated contexts
        return PASSWORD_MIN_LENGTH


def hash_password(plain: str) -> str:
    if not isinstance(plain, str) or not plain:
        raise ValueError("Password must be a non-empty string")
    bcrypt = _bcrypt()
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    if not isinstance(plain, str) or not isinstance(hashed, str) or not hashed:
        return False
    bcrypt = _bcrypt()
    try:
        return bool(bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8")))
    except (ValueError, TypeError):
        return False


def password_strength_errors(plain: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(plain, str):
        return ["Password must be a string"]

    minimum = _min_length()
    if len(plain) < minimum:
        errors.append(f"Password must be at least {minimum} characters long")
    if not any(ch.isalpha() for ch in plain):
        errors.append("Password must contain at least one letter")
    if not any(ch.isdigit() for ch in plain):
        errors.append("Password must contain at least one digit")
    if plain.lower() in _COMMON_PASSWORDS:
        errors.append("Password is too common — choose something less guessable")
    if plain.strip() != plain:
        errors.append("Password must not start or end with whitespace")
    return errors
