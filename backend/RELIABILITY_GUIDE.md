# Reliability Guide

## Overview

This document describes the reliability mechanisms implemented in ScamShield, covering failure handling, retry logic, circuit breakers, concurrency management, and recovery procedures.

## 1. Connector Reliability

### Retry Mechanism

All connector lookups use configurable automatic retry:

```
CONNECTOR_RETRY_COUNT = 1  (configurable via SCAMSHIELD_CONNECTOR_RETRY_COUNT)
```

- Failed lookups are retried up to `CONNECTOR_RETRY_COUNT + 1` times.
- After all retries are exhausted, a `LookupResult` with `error` set and `matched=False` is returned instead of raising an exception.
- Retry applies to transient errors (timeouts, connection resets, 5xx responses).
- Configuration is in `core/config/connectors.py` and overridable via environment variables.

### Timeout Handling

```
CONNECTOR_TIMEOUT = 10 seconds  (configurable via SCAMSHIELD_CONNECTOR_TIMEOUT)
```

- Each connector lookup has a hard timeout.
- `ThreadPoolExecutor.as_completed` is used with `timeout=CONNECTOR_TIMEOUT + 5` for overall parallel execution.
- Individual futures use `future.result(timeout=CONNECTOR_TIMEOUT)`.
- Timeouts produce a `LookupResult` with error `"Timeout after {timeout}s"`.

### Health Checks

- `ConnectorManager._check_health()` calls `connector.health()` before dispatching a lookup.
- Connectors returning `status` not in `("healthy", "ok", "available")` are skipped.
- Health failures produce a result with error `"Connector unhealthy"`.

### Parallelism

```
CONNECTOR_PARALLELISM = 4  (configurable via SCAMSHIELD_CONNECTOR_PARALLELISM)
```

- Connector lookups run in parallel using `ThreadPoolExecutor`.
- The number of concurrent connector lookups is capped by `CONNECTOR_PARALLELISM`.
- All results are merged and deduplicated.

### Caching

```
CONNECTOR_CACHE_TTL = 300 seconds  (configurable via SCAMSHIELD_CONNECTOR_CACHE_TTL)
```

- Successful lookup results are cached by `ConnectorCache`.
- Cache keys use `{connector_name}:{indicator_type}:{normalised_indicator}`.
- Entries expire after `CONNECTOR_CACHE_TTL` seconds.
- `purge_expired()` is called to clean stale entries.
- Cache capacity is unbounded (relies on TTL expiry).

## 2. Pipeline Reliability

### Step Execution

- Each pipeline step implements `execute()`, `initialize()`, and `cleanup()` lifecycle methods.
- Steps register with `StepRegistry` which validates ordering and dependency chains.
- Pipeline runner executes steps in registration order.

### Failure Isolation

- Pipeline step failures are caught and recorded without crashing the runner.
- Each step's `telemetry` captures `success`, `duration_ms`, and `error` fields.
- The pipeline produces a `PipelineResult` containing per-step telemetry even on partial failure.

### Optional Steps

- Steps can be marked as optional via `pipeline/step.py`.
- If an optional step fails, the pipeline continues execution.
- Non-optional step failures mark the pipeline as degraded.

## 3. Exception Hierarchy

```
ConnectorError (base)
  +-- ConnectorTimeoutError     (timeout during lookup)
  +-- ConnectorUnavailableError  (health check failure)
  +-- ConnectorLookupError       (unexpected lookup failure)
  +-- ConnectorConfigError       (invalid configuration)

PipelineError (base)
  +-- PipelineStepError        (step execution failure)
  +-- PipelineFatalError       (fatal pipeline failure)
  +-- PipelineDependencyError  (missing dependency)
```

## 4. Circuit Breaker (Planned)

A circuit breaker is not yet implemented but is planned for Sprint 3. The design will:

- Track consecutive failures per connector.
- Open circuit after N consecutive failures (configurable).
- Half-open after a cooldown period to test recovery.
- Close circuit on successful probe.

## 5. Concurrency Safe

- `ConnectorCache` uses `threading.Lock` for all store operations.
- `ConnectorRegistry` is class-level but designed for single-process use.
- `ConnectorManager._lookup_single` is thread-safe via `ThreadPoolExecutor`.
- `get_manager()` uses a module-level singleton with lazy initialisation.

## 6. Recovery Procedures

### After Connector Failure

1. Check `health_summary()` for connector status.
2. Verify network connectivity and API endpoints.
3. Increase `CONNECTOR_TIMEOUT` if timeouts are frequent.
4. Increase `CONNECTOR_RETRY_COUNT` for transient failures.

### After Pipeline Failure

1. Check step telemetry in `PipelineResult.steps_telemetry`.
2. Examine `telemetry["error"]` for failure details.
3. Verify step registration and dependencies.

### Cache Recovery

- Call `ConnectorCache.clear()` to flush all cached entries.
- Call `ConnectorCache.purge_expired()` to remove stale entries.
- Reduce `CONNECTOR_CACHE_TTL` during debugging.
