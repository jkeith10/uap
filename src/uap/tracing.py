"""Distributed tracing for UAP"""

from __future__ import annotations

import time
import uuid
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from contextvars import ContextVar
import asyncio

from .logging_config import get_logger

logger = get_logger(__name__)

# Context variables for tracing
trace_context: ContextVar[Optional[Dict[str, Any]]] = ContextVar('trace_context', default=None)
span_context: ContextVar[Optional[Dict[str, Any]]] = ContextVar('span_context', default=None)


@dataclass
class Span:
    """A tracing span"""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    operation_name: str = ""
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    duration: Optional[float] = None
    tags: Dict[str, Any] = field(default_factory=dict)
    logs: List[Dict[str, Any]] = field(default_factory=list)
    status: str = "ok"
    error_message: Optional[str] = None
    
    def finish(self, status: str = "ok", error_message: Optional[str] = None) -> None:
        """Finish the span"""
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        self.status = status
        self.error_message = error_message
    
    def add_tag(self, key: str, value: Any) -> None:
        """Add a tag to the span"""
        self.tags[key] = value
    
    def add_log(self, message: str, fields: Dict[str, Any] = None) -> None:
        """Add a log entry to the span"""
        log_entry = {
            "timestamp": time.time(),
            "message": message,
            "fields": fields or {}
        }
        self.logs.append(log_entry)


@dataclass
class Trace:
    """A distributed trace"""
    trace_id: str
    spans: List[Span] = field(default_factory=list)
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    duration: Optional[float] = None
    
    def add_span(self, span: Span) -> None:
        """Add a span to the trace"""
        self.spans.append(span)
    
    def finish(self) -> None:
        """Finish the trace"""
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time


class Tracer:
    """Distributed tracer"""
    
    def __init__(self):
        self._traces: Dict[str, Trace] = {}
        self._active_spans: Dict[str, Span] = {}
    
    def start_trace(self, trace_id: Optional[str] = None) -> str:
        """Start a new trace"""
        if trace_id is None:
            trace_id = str(uuid.uuid4())
        
        trace = Trace(trace_id=trace_id)
        self._traces[trace_id] = trace
        
        # Set trace context
        trace_context.set({"trace_id": trace_id})
        
        logger.debug("Started trace", trace_id=trace_id)
        return trace_id
    
    def start_span(
        self,
        operation_name: str,
        trace_id: Optional[str] = None,
        parent_span_id: Optional[str] = None,
        tags: Dict[str, Any] = None
    ) -> str:
        """Start a new span"""
        if trace_id is None:
            trace_id = trace_context.get()
            if trace_id is None:
                trace_id = self.start_trace()
        
        span_id = str(uuid.uuid4())
        span = Span(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            operation_name=operation_name,
            tags=tags or {}
        )
        
        # Add span to trace
        if trace_id in self._traces:
            self._traces[trace_id].add_span(span)
        
        # Set active span
        self._active_spans[span_id] = span
        span_context.set({"span_id": span_id, "trace_id": trace_id})
        
        logger.debug("Started span", trace_id=trace_id, span_id=span_id, operation=operation_name)
        return span_id
    
    def finish_span(
        self,
        span_id: str,
        status: str = "ok",
        error_message: Optional[str] = None
    ) -> None:
        """Finish a span"""
        if span_id in self._active_spans:
            span = self._active_spans[span_id]
            span.finish(status, error_message)
            del self._active_spans[span_id]
            
            logger.debug("Finished span", trace_id=span.trace_id, span_id=span_id, status=status)
    
    def add_span_tag(self, span_id: str, key: str, value: Any) -> None:
        """Add a tag to a span"""
        if span_id in self._active_spans:
            self._active_spans[span_id].add_tag(key, value)
    
    def add_span_log(self, span_id: str, message: str, fields: Dict[str, Any] = None) -> None:
        """Add a log entry to a span"""
        if span_id in self._active_spans:
            self._active_spans[span_id].add_log(message, fields)
    
    def get_trace(self, trace_id: str) -> Optional[Trace]:
        """Get a trace by ID"""
        return self._traces.get(trace_id)
    
    def get_active_span(self, span_id: str) -> Optional[Span]:
        """Get an active span by ID"""
        return self._active_spans.get(span_id)
    
    def get_current_span_id(self) -> Optional[str]:
        """Get current span ID from context"""
        context = span_context.get()
        return context.get("span_id") if context else None
    
    def get_current_trace_id(self) -> Optional[str]:
        """Get current trace ID from context"""
        context = trace_context.get()
        return context.get("trace_id") if context else None
    
    def finish_trace(self, trace_id: str) -> Optional[Trace]:
        """Finish a trace"""
        if trace_id in self._traces:
            trace = self._traces[trace_id]
            trace.finish()
            del self._traces[trace_id]
            
            logger.debug("Finished trace", trace_id=trace_id, duration=trace.duration)
            return trace
        return None
    
    def get_all_traces(self) -> Dict[str, Trace]:
        """Get all traces"""
        return self._traces.copy()
    
    def clear_traces(self) -> None:
        """Clear all traces"""
        self._traces.clear()
        self._active_spans.clear()


# Global tracer instance
_tracer = Tracer()


def get_tracer() -> Tracer:
    """Get global tracer instance"""
    return _tracer


def start_trace(trace_id: Optional[str] = None) -> str:
    """Start a new trace"""
    return _tracer.start_trace(trace_id)


def start_span(
    operation_name: str,
    trace_id: Optional[str] = None,
    parent_span_id: Optional[str] = None,
    tags: Dict[str, Any] = None
) -> str:
    """Start a new span"""
    return _tracer.start_span(operation_name, trace_id, parent_span_id, tags)


def finish_span(span_id: str, status: str = "ok", error_message: Optional[str] = None) -> None:
    """Finish a span"""
    _tracer.finish_span(span_id, status, error_message)


def add_span_tag(span_id: str, key: str, value: Any) -> None:
    """Add a tag to a span"""
    _tracer.add_span_tag(span_id, key, value)


def add_span_log(span_id: str, message: str, fields: Dict[str, Any] = None) -> None:
    """Add a log entry to a span"""
    _tracer.add_span_log(span_id, message, fields)


def get_current_span_id() -> Optional[str]:
    """Get current span ID from context"""
    return _tracer.get_current_span_id()


def get_current_trace_id() -> Optional[str]:
    """Get current trace ID from context"""
    return _tracer.get_current_trace_id()


def trace_function(operation_name: str, tags: Dict[str, Any] = None):
    """Decorator to trace function execution"""
    def decorator(func):
        if asyncio.iscoroutinefunction(func):
            async def async_wrapper(*args, **kwargs):
                span_id = start_span(operation_name, tags=tags)
                try:
                    result = await func(*args, **kwargs)
                    finish_span(span_id, "ok")
                    return result
                except Exception as e:
                    finish_span(span_id, "error", str(e))
                    raise
            return async_wrapper
        else:
            def sync_wrapper(*args, **kwargs):
                span_id = start_span(operation_name, tags=tags)
                try:
                    result = func(*args, **kwargs)
                    finish_span(span_id, "ok")
                    return result
                except Exception as e:
                    finish_span(span_id, "error", str(e))
                    raise
            return sync_wrapper
    return decorator


class TraceContext:
    """Context manager for tracing"""
    
    def __init__(self, operation_name: str, tags: Dict[str, Any] = None):
        self.operation_name = operation_name
        self.tags = tags or {}
        self.span_id: Optional[str] = None
    
    def __enter__(self) -> TraceContext:
        self.span_id = start_span(self.operation_name, tags=self.tags)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.span_id:
            if exc_type is not None:
                finish_span(self.span_id, "error", str(exc_val))
            else:
                finish_span(self.span_id, "ok")
    
    async def __aenter__(self) -> TraceContext:
        self.span_id = start_span(self.operation_name, tags=self.tags)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.span_id:
            if exc_type is not None:
                finish_span(self.span_id, "error", str(exc_val))
            else:
                finish_span(self.span_id, "ok")
