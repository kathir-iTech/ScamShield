# CI Quality Gates

This document outlines the quality gates that must be met for code to be merged and deployed. These gates ensure the stability, reliability, and maintainability of the ScamShield project.

## 1. Test Execution
- **All tests must pass:** The entire test suite (unit, integration, security, reliability, chaos, performance) must pass without any failures.
- **Exit code 0:** The test runner must exit with a status code of 0.

## 2. Test Coverage
- **Minimum coverage:** A minimum of **85% line coverage** for Python code is required.
- **Targeted improvement:** Any module falling below **75% coverage** will be flagged.
- **No regressions:** Coverage must not decrease compared to the previous baseline. The CI pipeline will fail if coverage drops.

## 3. Security Standards
- **Security tests pass:** All tests in `tests/security/` must pass.
- **Dependency scanning:** Dependency vulnerability scanning tools (e.g., `pip-audit`, `npm audit`) must pass with no critical or high severity vulnerabilities.
- **Static analysis:** Static code analysis tools (e.g., Ruff for Python, ESLint/TypeScript for frontend) must find no critical or high severity issues.
- **Secrets scanning:** Automated secrets scanning (e.g., `git-secrets`, `trufflehog`) must detect no secrets in the codebase or commit history.

## 4. Performance Benchmarks
- **Benchmark suite operational:** Performance benchmarks must execute successfully.
- **No regressions:** Key performance metrics (e.g., latency, memory usage, CPU utilization) must not degrade beyond defined thresholds. Benchmarks will track:
    - Text analysis latency (P95 < 1000ms, P50 < 500ms)
    - Pipeline execution time
    - Rule execution time
    - Entity extraction time
    - Knowledge retrieval time
- **Threshold enforcement:** The CI pipeline will fail if performance regressions exceed thresholds.

## 5. Code Quality
- **Static analysis:** Linting and type-checking tools (Ruff, MyPy for Python; ESLint, TypeScript for frontend) must pass without errors.
- **Code style:** Code must adhere to project conventions (PEP 8 for Python, Prettier/ESLint for TS/JS).
- **No deprecations:** Avoid using deprecated libraries or language features.

## 6. Documentation
- **Required documentation:** All new or significantly modified code must have appropriate documentation (docstrings, READMEs).
- **Test strategy:** `TEST_STRATEGY.md` must be kept up-to-date.
- **Coverage report:** `TEST_COVERAGE_REPORT.md` must reflect current coverage.
- **Reliability guide:** `RELIABILITY_GUIDE.md` must be updated.
- **CI quality gates:** `QUALITY_GATES.md` is this document.

## Enforcement
- **CI Pipeline:** All quality gates will be enforced in the CI pipeline.
- **Merge blocking:** Commits that fail any quality gate will block merging to the main branch. Automated checks will prevent merging.
- **Review process:** Code reviews will verify adherence to these quality gates.
