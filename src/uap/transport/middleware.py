"""Middleware for UAP Transport Layer"""

import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add correlation IDs to requests"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate or extract correlation ID
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        
        # Add to request state
        request.state.correlation_id = correlation_id
        
        # Process request
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Add correlation ID to response headers
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Process-Time"] = str(process_time)
        
        # Log request
        logger.info(
            "Request processed",
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            process_time=process_time,
            correlation_id=correlation_id
        )
        
        return response


class OpenTelemetryMiddleware(BaseHTTPMiddleware):
    """OpenTelemetry middleware for distributed tracing"""
    
    def __init__(self, app, tracer=None):
        super().__init__(app)
        self.tracer = tracer
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if self.tracer:
            with self.tracer.start_as_current_span(
                f"{request.method} {request.url.path}"
            ) as span:
                span.set_attribute("http.method", request.method)
                span.set_attribute("http.url", str(request.url))
                span.set_attribute("correlation_id", getattr(request.state, "correlation_id", ""))
                
                response = await call_next(request)
                
                span.set_attribute("http.status_code", response.status_code)
                return response
        else:
            return await call_next(request)


def setup_middleware(app, tracer=None):
    """Setup middleware for the FastAPI application"""
    
    # Add correlation ID middleware
    app.add_middleware(CorrelationIDMiddleware)
    
    # Add OpenTelemetry middleware if tracer is provided
    if tracer:
        app.add_middleware(OpenTelemetryMiddleware, tracer=tracer)
    
    return app
