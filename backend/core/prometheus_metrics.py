import time
from typing import Dict, Optional

from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST

from core.metrics import metrics

_initialized: bool = False
_last_snapshot: Dict[str, int] = {}

scamshield_requests_total: Optional[Counter] = None
scamshield_request_duration_seconds: Optional[Histogram] = None
scamshield_active_requests: Optional[Gauge] = None
scamshield_validation_failures_total: Optional[Counter] = None
scamshield_auth_failures_total: Optional[Counter] = None
scamshield_rate_limit_events_total: Optional[Counter] = None
scamshield_pipeline_failures_total: Optional[Counter] = None
scamshield_pipeline_stage_duration_seconds: Optional[Histogram] = None
scamshield_ocr_requests_total: Optional[Counter] = None
scamshield_text_requests_total: Optional[Counter] = None
scamshield_model_info: Optional[Gauge] = None
scamshield_memory_usage_bytes: Optional[Gauge] = None
scamshield_cpu_percent: Optional[Gauge] = None
scamshield_process_memory_bytes: Optional[Gauge] = None
scamshield_process_cpu_percent: Optional[Gauge] = None
scamshield_process_threads: Optional[Gauge] = None
scamshield_process_fds: Optional[Gauge] = None


def _sync_counter_from_snapshot(
    counter: Counter, snapshot_key: str,
) -> None:
    val = metrics.snapshot().get(snapshot_key, 0)
    last_val = _last_snapshot.get(snapshot_key, 0)
    delta = val - last_val
    if delta > 0:
        counter.inc(delta)
    elif delta < 0:
        pass
    _last_snapshot[snapshot_key] = val


def init_prometheus_metrics() -> None:
    global _initialized
    global scamshield_requests_total
    global scamshield_request_duration_seconds
    global scamshield_active_requests
    global scamshield_validation_failures_total
    global scamshield_auth_failures_total
    global scamshield_rate_limit_events_total
    global scamshield_pipeline_failures_total
    global scamshield_pipeline_stage_duration_seconds
    global scamshield_ocr_requests_total
    global scamshield_text_requests_total
    global scamshield_model_info
    global scamshield_memory_usage_bytes
    global scamshield_cpu_percent
    global scamshield_process_memory_bytes
    global scamshield_process_cpu_percent
    global scamshield_process_threads
    global scamshield_process_fds

    if _initialized:
        return

    scamshield_requests_total = Counter(
        "scamshield_requests_total",
        "Total number of requests",
        labelnames=["method", "path", "status"],
    )
    scamshield_request_duration_seconds = Histogram(
        "scamshield_request_duration_seconds",
        "Request duration in seconds",
        buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
    )
    scamshield_active_requests = Gauge(
        "scamshield_active_requests",
        "Current number of active requests",
    )
    scamshield_validation_failures_total = Counter(
        "scamshield_validation_failures_total",
        "Total number of validation failures",
    )
    scamshield_auth_failures_total = Counter(
        "scamshield_auth_failures_total",
        "Total number of authentication failures",
    )
    scamshield_rate_limit_events_total = Counter(
        "scamshield_rate_limit_events_total",
        "Total number of rate limit events",
    )
    scamshield_pipeline_failures_total = Counter(
        "scamshield_pipeline_failures_total",
        "Total number of pipeline failures",
    )
    scamshield_pipeline_stage_duration_seconds = Histogram(
        "scamshield_pipeline_stage_duration_seconds",
        "Pipeline stage duration in seconds",
        labelnames=["stage"],
        buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
    )
    scamshield_ocr_requests_total = Counter(
        "scamshield_ocr_requests_total",
        "Total number of OCR requests",
    )
    scamshield_text_requests_total = Counter(
        "scamshield_text_requests_total",
        "Total number of text requests",
    )
    scamshield_model_info = Gauge(
        "scamshield_model_info",
        "Model version and status information",
        labelnames=["version", "status"],
    )
    scamshield_memory_usage_bytes = Gauge(
        "scamshield_memory_usage_bytes",
        "System memory usage in bytes",
    )
    scamshield_cpu_percent = Gauge(
        "scamshield_cpu_percent",
        "System CPU usage percent",
    )
    scamshield_process_memory_bytes = Gauge(
        "scamshield_process_memory_bytes",
        "Process memory usage in bytes",
    )
    scamshield_process_cpu_percent = Gauge(
        "scamshield_process_cpu_percent",
        "Process CPU usage percent",
    )
    scamshield_process_threads = Gauge(
        "scamshield_process_threads",
        "Number of process threads",
    )
    scamshield_process_fds = Gauge(
        "scamshield_process_fds",
        "Number of open file descriptors",
    )

    _initialized = True


def update_prometheus_metrics() -> None:
    if not _initialized:
        return

    snapshot = metrics.snapshot()
    system = snapshot.get("system", {})

    scamshield_active_requests.set(snapshot.get("active_requests", 0))

    _sync_counter_from_snapshot(scamshield_validation_failures_total, "validation_failures")
    _sync_counter_from_snapshot(scamshield_auth_failures_total, "auth_failures")
    _sync_counter_from_snapshot(scamshield_rate_limit_events_total, "rate_limit_events")
    _sync_counter_from_snapshot(scamshield_pipeline_failures_total, "pipeline_failures")
    _sync_counter_from_snapshot(scamshield_ocr_requests_total, "ocr_requests")
    _sync_counter_from_snapshot(scamshield_text_requests_total, "text_requests")

    memory = system.get("memory", {})
    if memory:
        scamshield_memory_usage_bytes.set(memory.get("total_gb", 0) * (1024**3))

    cpu = system.get("cpu", {})
    if cpu:
        scamshield_cpu_percent.set(cpu.get("percent", 0))

    proc = system.get("process", {})
    if proc:
        scamshield_process_memory_bytes.set(proc.get("memory_mb", 0) * (1024**2))
        scamshield_process_cpu_percent.set(proc.get("cpu_percent", 0))
        scamshield_process_threads.set(proc.get("threads", 0))
        scamshield_process_fds.set(proc.get("open_fds", 0))


def record_prometheus_request(method: str, path: str, status: int, duration: float) -> None:
    if not _initialized:
        return
    scamshield_requests_total.labels(method=method, path=path, status=str(status)).inc()
    scamshield_request_duration_seconds.observe(duration)


def record_prometheus_stage(stage: str, duration: float) -> None:
    if not _initialized:
        return
    scamshield_pipeline_stage_duration_seconds.labels(stage=stage).observe(duration)


def get_prometheus_metrics_endpoint() -> tuple:
    if not _initialized:
        init_prometheus_metrics()
    update_prometheus_metrics()
    return generate_latest(), CONTENT_TYPE_LATEST
