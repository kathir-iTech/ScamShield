import os
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class StageTiming:
    stage: str
    elapsed_ms: float


class Metrics:
    def __init__(self, window_size: int = 1000) -> None:
        self._lock = threading.Lock()
        self._window_size = window_size

        self.total_requests: int = 0
        self.successful_requests: int = 0
        self.failed_requests: int = 0
        self.validation_failures: int = 0
        self.ocr_requests: int = 0
        self.text_requests: int = 0
        self.active_requests: int = 0
        self.auth_failures: int = 0
        self.rate_limit_events: int = 0
        self.pipeline_failures: int = 0
        self._startup_time: float = time.time()

        self._latencies: List[float] = []
        self._stage_timings: Dict[str, List[float]] = {}

    def record_request_start(self) -> None:
        with self._lock:
            self.active_requests += 1

    def record_request_end(self) -> None:
        with self._lock:
            if self.active_requests > 0:
                self.active_requests -= 1

    def record_request(
        self, elapsed_ms: float, success: bool, is_ocr: bool, is_validation_failure: bool
    ) -> None:
        with self._lock:
            self.total_requests += 1
            if success:
                self.successful_requests += 1
            else:
                self.failed_requests += 1
            if is_validation_failure:
                self.validation_failures += 1
            if is_ocr:
                self.ocr_requests += 1
            else:
                self.text_requests += 1
            self._latencies.append(elapsed_ms)
            if len(self._latencies) > self._window_size:
                self._latencies.pop(0)

    def record_stage(self, stage: str, elapsed_ms: float) -> None:
        with self._lock:
            if stage not in self._stage_timings:
                self._stage_timings[stage] = []
            self._stage_timings[stage].append(elapsed_ms)
            if len(self._stage_timings[stage]) > self._window_size:
                self._stage_timings[stage].pop(0)

    def record_auth_failure(self) -> None:
        with self._lock:
            self.auth_failures += 1

    def record_rate_limit_event(self) -> None:
        with self._lock:
            self.rate_limit_events += 1

    def record_pipeline_failure(self) -> None:
        with self._lock:
            self.pipeline_failures += 1

    @property
    def average_latency_ms(self) -> float:
        with self._lock:
            if not self._latencies:
                return 0.0
            return sum(self._latencies) / len(self._latencies)

    @property
    def p50_latency_ms(self) -> float:
        with self._lock:
            if not self._latencies:
                return 0.0
            sorted_lat = sorted(self._latencies)
            return sorted_lat[len(sorted_lat) // 2]

    @property
    def p95_latency_ms(self) -> float:
        with self._lock:
            if not self._latencies:
                return 0.0
            sorted_lat = sorted(self._latencies)
            idx = int(len(sorted_lat) * 0.95)
            return sorted_lat[idx] if idx < len(sorted_lat) else sorted_lat[-1]

    @property
    def maximum_latency_ms(self) -> float:
        with self._lock:
            return max(self._latencies) if self._latencies else 0.0

    @property
    def uptime_seconds(self) -> float:
        return time.time() - self._startup_time

    @property
    def pipeline_stage_timings(self) -> Dict[str, Dict]:
        with self._lock:
            result = {}
            for stage, timings in self._stage_timings.items():
                if timings:
                    sorted_t = sorted(timings)
                    result[stage] = {
                        "avg_ms": round(sum(timings) / len(timings), 1),
                        "p50_ms": round(sorted_t[len(sorted_t) // 2], 1),
                        "p95_ms": round(sorted_t[int(len(sorted_t) * 0.95)], 1),
                        "count": len(timings),
                    }
            return result

    def _get_system_metrics(self) -> Dict[str, Any]:
        result = {}
        try:
            import psutil
            mem = psutil.virtual_memory()
            cpu = psutil.cpu_percent(interval=None)
            result["memory"] = {
                "total_gb": round(mem.total / (1024**3), 1),
                "available_gb": round(mem.available / (1024**3), 1),
                "percent_used": mem.percent,
            }
            result["cpu"] = {
                "percent": cpu,
            }
            proc = psutil.Process()
            result["process"] = {
                "memory_mb": round(proc.memory_info().rss / (1024**2), 1),
                "cpu_percent": proc.cpu_percent(interval=None),
                "open_fds": proc.num_fds() if hasattr(proc, "num_fds") else 0,
                "threads": proc.num_threads(),
            }
        except ImportError:
            pass
        except Exception:
            pass
        return result

    def snapshot(self) -> Dict:
        result = {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "active_requests": self.active_requests,
            "validation_failures": self.validation_failures,
            "auth_failures": self.auth_failures,
            "rate_limit_events": self.rate_limit_events,
            "pipeline_failures": self.pipeline_failures,
            "ocr_requests": self.ocr_requests,
            "text_requests": self.text_requests,
            "average_latency_ms": round(self.average_latency_ms, 1),
            "p50_latency_ms": round(self.p50_latency_ms, 1),
            "p95_latency_ms": round(self.p95_latency_ms, 1),
            "maximum_latency_ms": round(self.maximum_latency_ms, 1),
            "uptime_seconds": round(self.uptime_seconds, 1),
        }
        system = self._get_system_metrics()
        if system:
            result["system"] = system
        return result


metrics = Metrics()
