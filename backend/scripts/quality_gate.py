import importlib
import os
import subprocess
import sys
import traceback
from typing import Callable, List, Tuple


def _check_pytest() -> bool:
    print("=== CHECK: pytest passes ===")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-x", "-q", "--tb=short"],
        capture_output=True,
        text=True,
        cwd=os.path.join(os.path.dirname(__file__), ".."),
    )
    if result.returncode != 0:
        print("FAIL: pytest exited with code", result.returncode)
        print(result.stdout[-2000:])
        print(result.stderr[-2000:])
        return False
    print("PASS: all tests pass")
    return True


def _check_imports() -> bool:
    print("=== CHECK: all imports succeed ===")
    modules = [
        "core.constants",
        "core.exceptions",
        "core.logger",
        "core.metrics",
        "core.diagnostics",
        "core.middleware",
        "config.settings",
        "services.orchestrator",
        "services.ml_service",
        "services.rules_service",
        "services.explanation_service",
        "services.intelligence_service",
        "services.evidence_service",
        "services.assessment_service",
        "services.report_service",
        "services.ocr_service",
        "routers.health",
        "routers.analyze",
        "schemas.requests",
        "schemas.responses",
        "utils.validate",
        "predict",
    ]
    ok = True
    for mod in modules:
        try:
            importlib.import_module(mod)
            print(f"  OK: {mod}")
        except Exception:
            print(f"  FAIL: {mod}")
            traceback.print_exc()
            ok = False
    return ok


def _check_config_loads() -> bool:
    print("=== CHECK: configuration loads ===")
    try:
        from config import settings
        _ = settings.MAX_TEXT_LENGTH
        _ = settings.MAX_FILE_SIZE_MB
        _ = settings.SUPPORTED_IMAGE_TYPES
        print(f"  MAX_TEXT_LENGTH={settings.MAX_TEXT_LENGTH}")
        print(f"  MAX_FILE_SIZE_MB={settings.MAX_FILE_SIZE_MB}")
        print(f"  SUPPORTED_IMAGE_TYPES={settings.SUPPORTED_IMAGE_TYPES}")
        print("PASS: configuration loads successfully")
        return True
    except Exception:
        traceback.print_exc()
        return False


def _check_models_exist() -> bool:
    print("=== CHECK: model artefacts exist ===")
    from config import settings
    errors = []
    if not os.path.isfile(settings.MODEL_PATH):
        errors.append(f"Model not found: {settings.MODEL_PATH}")
    else:
        print(f"  OK: model at {settings.MODEL_PATH}")
    if not os.path.isfile(settings.VECTORIZER_PATH):
        errors.append(f"Vectorizer not found: {settings.VECTORIZER_PATH}")
    else:
        print(f"  OK: vectorizer at {settings.VECTORIZER_PATH}")
    if errors:
        for e in errors:
            print(f"  FAIL: {e}")
        return False
    print("PASS: all model artefacts exist")
    return True


def _check_openapi() -> bool:
    print("=== CHECK: OpenAPI generation ===")
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
        from main import app
        spec = app.openapi()
        required_paths = ["/health", "/ready", "/live", "/analyze/text", "/analyze/image", "/metrics"]
        missing = [p for p in required_paths if p not in spec.get("paths", {})]
        if missing:
            print(f"  FAIL: missing paths: {missing}")
            return False
        for p in required_paths:
            print(f"  OK: path {p}")
        print("PASS: OpenAPI spec generated with all required routes")
        return True
    except Exception:
        traceback.print_exc()
        return False


def _check_response_schemas() -> bool:
    print("=== CHECK: response schemas ===")
    try:
        from main import app
        spec = app.openapi()
        schemas = spec.get("components", {}).get("schemas", {})
        required = ["AnalysisResponse", "ImageAnalysisResponse"]
        missing = [s for s in required if s not in schemas]
        if missing:
            print(f"  FAIL: missing schemas: {missing}")
            return False
        for s in required:
            print(f"  OK: schema {s}")
        print("PASS: all required response schemas defined")
        return True
    except Exception:
        traceback.print_exc()
        return False


def _check_documentation_exists() -> bool:
    print("=== CHECK: documentation exists ===")
    base = os.path.dirname(os.path.dirname(__file__))
    parent = os.path.dirname(base)
    required_docs = [
        "ARCHITECTURE_REVIEW.md",
        "PRODUCTION_HARDENING.md",
        "ENGINEERING_DECISIONS.md",
        "RELEASE_READINESS.md",
    ]
    ok = True
    for doc in required_docs:
        path = os.path.join(base, doc)
        if not os.path.isfile(path):
            path = os.path.join(parent, doc)
        if os.path.isfile(path):
            print(f"  OK: {doc}")
        else:
            print(f"  FAIL: {doc} not found")
            ok = False
    return ok


def _check_no_circular_imports() -> bool:
    print("=== CHECK: no circular imports ===")
    modules = [
        "core",
        "config",
        "services",
        "routers",
        "schemas",
        "utils",
    ]
    for mod_name in modules:
        try:
            importlib.import_module(mod_name)
            print(f"  OK: {mod_name}")
        except ImportError as e:
            if "circular" in str(e).lower():
                print(f"  FAIL: circular import in {mod_name}: {e}")
                return False
            print(f"  OK: {mod_name} (non-critical import issue: {e})")
    print("PASS: no circular imports detected")
    return True


def _check_no_duplicated_constants() -> bool:
    print("=== CHECK: no duplicated constants ===")
    const_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "core", "constants.py")
    if not os.path.isfile(const_file):
        print("  FAIL: constants.py not found")
        return False
    with open(const_file) as f:
        content = f.read()
    suspicious_dups = ["SEVERITY_", "PRIORITY_", "DECISION_", "ASSESSMENT_", "CONFIDENCE_", "ACTION_", "RISK_"]
    ok = True
    for prefix in suspicious_dups:
        lines = [l.strip() for l in content.splitlines() if l.strip().startswith(f"{prefix}") and "=" in l]
        values = {}
        for line in lines:
            parts = line.split("=", 1)
            if len(parts) == 2:
                val = parts[1].strip().strip('"\'')
                if val in values:
                    print(f"  WARN: {prefix} duplicate value '{val}' at: {values[val]} and {line}")
                    ok = False
                values[val] = line
    if ok:
        print("PASS: no duplicated constants")
    return ok


def main() -> int:
    base = os.path.dirname(os.path.dirname(__file__))
    os.chdir(base)
    sys.path.insert(0, base)

    checks = [
        ("pytest passes", _check_pytest),
        ("imports succeed", _check_imports),
        ("configuration loads", _check_config_loads),
        ("model artefacts exist", _check_models_exist),
        ("OpenAPI generation", _check_openapi),
        ("response schemas defined", _check_response_schemas),
        ("documentation exists", _check_documentation_exists),
        ("no circular imports", _check_no_circular_imports),
        ("no duplicated constants", _check_no_duplicated_constants),
    ]

    failures = 0
    for name, check in checks:
        print(f"\n{'='*60}")
        print(f"CHECK: {name}")
        print(f"{'='*60}")
        try:
            if check():
                print(f"RESULT: {name} — PASS\n")
            else:
                print(f"RESULT: {name} — FAIL\n")
                failures += 1
        except Exception:
            print(f"RESULT: {name} — EXCEPTION\n")
            traceback.print_exc()
            failures += 1

    print(f"\n{'='*60}")
    print(f"QUALITY GATE SUMMARY: {len(checks) - failures}/{len(checks)} passed")
    if failures:
        print(f"FAILURES: {failures}")
    print(f"{'='*60}")
    return 1 if failures > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
