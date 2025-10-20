"""Metrics collection and monitoring for UAP"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from collections import defaultdict, deque
from threading import Lock
import asyncio

from .logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class MetricValue:
    """A metric value with timestamp"""
    value: float
    timestamp: float = field(default_factory=time.time)
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class Counter:
    """Counter metric"""
    name: str
    value: float = 0.0
    labels: Dict[str, str] = field(default_factory=dict)
    
    def increment(self, amount: float = 1.0) -> None:
        """Increment counter by amount"""
        self.value += amount
    
    def reset(self) -> None:
        """Reset counter to zero"""
        self.value = 0.0


@dataclass
class Gauge:
    """Gauge metric"""
    name: str
    value: float = 0.0
    labels: Dict[str, str] = field(default_factory=dict)
    
    def set(self, value: float) -> None:
        """Set gauge value"""
        self.value = value
    
    def increment(self, amount: float = 1.0) -> None:
        """Increment gauge by amount"""
        self.value += amount
    
    def decrement(self, amount: float = 1.0) -> None:
        """Decrement gauge by amount"""
        self.value -= amount


@dataclass
class Histogram:
    """Histogram metric"""
    name: str
    buckets: List[float] = field(default_factory=lambda: [0.1, 0.5, 1.0, 2.5, 5.0, 10.0])
    values: deque = field(default_factory=lambda: deque(maxlen=1000))
    labels: Dict[str, str] = field(default_factory=dict)
    
    def observe(self, value: float) -> None:
        """Observe a value"""
        self.values.append(value)
    
    def get_bucket_counts(self) -> Dict[str, int]:
        """Get counts for each bucket"""
        counts = {}
        for bucket in self.buckets:
            count = sum(1 for v in self.values if v <= bucket)
            counts[f"le_{bucket}"] = count
        counts["le_inf"] = len(self.values)
        return counts


@dataclass
class Summary:
    """Summary metric"""
    name: str
    values: deque = field(default_factory=lambda: deque(maxlen=1000))
    labels: Dict[str, str] = field(default_factory=dict)
    
    def observe(self, value: float) -> None:
        """Observe a value"""
        self.values.append(value)
    
    def get_quantiles(self, quantiles: List[float] = None) -> Dict[str, float]:
        """Get quantile values"""
        if quantiles is None:
            quantiles = [0.5, 0.9, 0.95, 0.99]
        
        if not self.values:
            return {f"quantile_{q}": 0.0 for q in quantiles}
        
        sorted_values = sorted(self.values)
        n = len(sorted_values)
        
        result = {}
        for q in quantiles:
            index = int(q * (n - 1))
            result[f"quantile_{q}"] = sorted_values[index]
        
        return result


class MetricsCollector:
    """Metrics collector and registry"""
    
    def __init__(self):
        self._counters: Dict[str, Counter] = {}
        self._gauges: Dict[str, Gauge] = {}
        self._histograms: Dict[str, Histogram] = {}
        self._summaries: Dict[str, Summary] = {}
        self._lock = Lock()
    
    def counter(self, name: str, labels: Dict[str, str] = None) -> Counter:
        """Get or create a counter"""
        key = self._make_key(name, labels or {})
        with self._lock:
            if key not in self._counters:
                self._counters[key] = Counter(name, labels=labels or {})
            return self._counters[key]
    
    def gauge(self, name: str, labels: Dict[str, str] = None) -> Gauge:
        """Get or create a gauge"""
        key = self._make_key(name, labels or {})
        with self._lock:
            if key not in self._gauges:
                self._gauges[key] = Gauge(name, labels=labels or {})
            return self._gauges[key]
    
    def histogram(self, name: str, labels: Dict[str, str] = None) -> Histogram:
        """Get or create a histogram"""
        key = self._make_key(name, labels or {})
        with self._lock:
            if key not in self._histograms:
                self._histograms[key] = Histogram(name, labels=labels or {})
            return self._histograms[key]
    
    def summary(self, name: str, labels: Dict[str, str] = None) -> Summary:
        """Get or create a summary"""
        key = self._make_key(name, labels or {})
        with self._lock:
            if key not in self._summaries:
                self._summaries[key] = Summary(name, labels=labels or {})
            return self._summaries[key]
    
    def _make_key(self, name: str, labels: Dict[str, str]) -> str:
        """Make a key for metric storage"""
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all metrics in Prometheus format"""
        with self._lock:
            metrics = {}
            
            # Counters
            for key, counter in self._counters.items():
                metrics[f"{counter.name}_total"] = {
                    "value": counter.value,
                    "labels": counter.labels
                }
            
            # Gauges
            for key, gauge in self._gauges.items():
                metrics[gauge.name] = {
                    "value": gauge.value,
                    "labels": gauge.labels
                }
            
            # Histograms
            for key, histogram in self._histograms.items():
                bucket_counts = histogram.get_bucket_counts()
                for bucket, count in bucket_counts.items():
                    metrics[f"{histogram.name}_bucket"] = {
                        "value": count,
                        "labels": {**histogram.labels, "le": bucket}
                    }
                metrics[f"{histogram.name}_count"] = {
                    "value": len(histogram.values),
                    "labels": histogram.labels
                }
                metrics[f"{histogram.name}_sum"] = {
                    "value": sum(histogram.values),
                    "labels": histogram.labels
                }
            
            # Summaries
            for key, summary in self._summaries.items():
                quantiles = summary.get_quantiles()
                for quantile, value in quantiles.items():
                    metrics[f"{summary.name}"] = {
                        "value": value,
                        "labels": {**summary.labels, "quantile": quantile}
                    }
                metrics[f"{summary.name}_count"] = {
                    "value": len(summary.values),
                    "labels": summary.labels
                }
                metrics[f"{summary.name}_sum"] = {
                    "value": sum(summary.values),
                    "labels": summary.labels
                }
            
            return metrics
    
    def reset(self) -> None:
        """Reset all metrics"""
        with self._lock:
            for counter in self._counters.values():
                counter.reset()
            for gauge in self._gauges.values():
                gauge.set(0.0)
            for histogram in self._histograms.values():
                histogram.values.clear()
            for summary in self._summaries.values():
                summary.values.clear()


# Global metrics collector
_metrics_collector = MetricsCollector()


def get_metrics_collector() -> MetricsCollector:
    """Get global metrics collector"""
    return _metrics_collector


def counter(name: str, labels: Dict[str, str] = None) -> Counter:
    """Get or create a counter"""
    return _metrics_collector.counter(name, labels)


def gauge(name: str, labels: Dict[str, str] = None) -> Gauge:
    """Get or create a gauge"""
    return _metrics_collector.gauge(name, labels)


def histogram(name: str, labels: Dict[str, str] = None) -> Histogram:
    """Get or create a histogram"""
    return _metrics_collector.histogram(name, labels)


def summary(name: str, labels: Dict[str, str] = None) -> Summary:
    """Get or create a summary"""
    return _metrics_collector.summary(name, labels)


def time_function(func: Callable) -> Callable:
    """Decorator to time function execution"""
    if asyncio.iscoroutinefunction(func):
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                histogram(f"{func.__name__}_duration").observe(duration)
        return async_wrapper
    else:
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                histogram(f"{func.__name__}_duration").observe(duration)
        return sync_wrapper


def count_calls(func: Callable) -> Callable:
    """Decorator to count function calls"""
    if asyncio.iscoroutinefunction(func):
        async def async_wrapper(*args, **kwargs):
            counter(f"{func.__name__}_calls").increment()
            return await func(*args, **kwargs)
        return async_wrapper
    else:
        def sync_wrapper(*args, **kwargs):
            counter(f"{func.__name__}_calls").increment()
            return func(*args, **kwargs)
        return sync_wrapper


def count_errors(func: Callable) -> Callable:
    """Decorator to count function errors"""
    if asyncio.iscoroutinefunction(func):
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                counter(f"{func.__name__}_errors").increment()
                raise
        return async_wrapper
    else:
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                counter(f"{func.__name__}_errors").increment()
                raise
        return sync_wrapper
