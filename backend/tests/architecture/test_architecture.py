import os
import sys
from pathlib import Path

import pytest

BASE = Path(__file__).resolve().parent.parent.parent


def _count_lines(path: Path) -> int:
    with open(path, encoding="utf-8") as f:
        return sum(1 for _ in f)


def test_no_service_exceeds_250_lines():
    services_dir = BASE / "services"
    if not services_dir.is_dir():
        return
    oversize = []
    for fpath in sorted(services_dir.rglob("*.py")):
        if fpath.name == "__init__.py":
            continue
        if fpath.stat().st_size == 0:
            continue
        lines = _count_lines(fpath)
        if lines > 250:
            rel = fpath.relative_to(BASE)
            oversize.append(f"{rel} ({lines} lines)")
    assert not oversize, f"Services exceeding 250 lines:\n" + "\n".join(oversize)


def test_no_circular_imports():
    all_importable = [
        "core.config.assessment",
        "core.config.connectors",
        "core.config.evaluation",
        "core.config.investigation",
        "core.config.knowledge",
        "core.config.reasoning",
        "core.config.refinement",
        "core.config.reporting",
        "core.config.validation",
        "core.config.pipeline",
        "core.constants.extraction",
        "core.constants.categories",
        "core.constants.indicators",
        "core.constants.evidence",
        "core.constants.labels",
        "core.constants.domain",
        "domains.shared.models",
        "domains.shared.utils",
        "domains.shared.exceptions",
        "domains.shared.public",
        "domains.knowledge.matcher",
        "domains.knowledge.search",
        "domains.knowledge.advisory",
        "domains.knowledge.enrichment",
        "domains.knowledge.service",
        "domains.knowledge.public",
        "domains.reasoning.graph",
        "domains.reasoning.refinement",
        "domains.reasoning.service",
        "domains.reasoning.public",
        "domains.intelligence.extractors",
        "domains.intelligence.service",
        "domains.intelligence.public",
        "domains.assessment.evidence",
        "domains.assessment.explanation",
        "domains.assessment.service",
        "domains.assessment.public",
        "domains.investigation.models",
        "domains.investigation.entities",
        "domains.investigation.timeline",
        "domains.investigation.campaign",
        "domains.investigation.graph",
        "domains.investigation.risk",
        "domains.investigation.service",
        "domains.investigation.public",
        "domains.reporting.sections",
        "domains.reporting.service",
        "domains.reporting.public",
        "services.threat_intelligence_service",
        "services.orchestrator",
    ]
    import importlib
    failed = []
    for mod_name in all_importable:
        try:
            importlib.import_module(mod_name)
        except ImportError as e:
            failed.append(f"{mod_name}: {e}")
    assert not failed, "Import failures (potential circular deps):\n" + "\n".join(failed)


def test_each_domain_has_public_py():
    domains_dir = BASE / "domains"
    if not domains_dir.is_dir():
        return
    missing = []
    for d in sorted(domains_dir.iterdir()):
        if d.is_dir() and not d.name.startswith("_"):
            public_py = d / "public.py"
            if not public_py.exists():
                missing.append(d.name)
    assert not missing, f"Domains missing public.py: {missing}"


def test_no_pass_through_wrappers_remain():
    services_dir = BASE / "services"
    wrappers = ["ml_service.py", "rules_service.py", "ocr_service.py"]
    found = []
    for w in wrappers:
        if (services_dir / w).exists():
            found.append(w)
    assert not found, f"Pass-through wrappers still present: {found}"


def test_domain_dependency_direction():
    domain_dirs = {"knowledge", "reasoning", "intelligence", "assessment", "investigation", "reporting", "shared"}
    forbidden_prefixes = {"routers", "pipeline"}

    for domain in domain_dirs:
        domain_path = BASE / "domains" / domain
        if not domain_path.is_dir():
            continue
        for py_file in domain_path.rglob("*.py"):
            content = py_file.read_text(encoding="utf-8")
            for line in content.splitlines():
                stripped = line.strip()
                if stripped.startswith("from ") or stripped.startswith("import "):
                    for prefix in forbidden_prefixes:
                        if f"import {prefix}" in stripped or f"from {prefix}" in stripped:
                            rel = py_file.relative_to(BASE)
                            assert False, f"{rel}: imports from forbidden layer '{prefix}'"


def test_domains_import_constants_from_core():
    domain_dirs = {"knowledge", "reasoning", "intelligence", "assessment", "investigation", "reporting"}

    for domain in domain_dirs:
        domain_path = BASE / "domains" / domain
        if not domain_path.is_dir():
            continue
        for py_file in domain_path.rglob("*.py"):
            content = py_file.read_text(encoding="utf-8")
            for line in content.splitlines():
                if "from domains.shared.constants" in line or "import domains.shared.constants" in line:
                    rel = py_file.relative_to(BASE)
                    assert False, f"{rel}: imports from deleted domains.shared.constants; use core.constants"
