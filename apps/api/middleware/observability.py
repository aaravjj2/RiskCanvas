"""
Structured logging and observability for RiskCanvas
"""

import os
import logging
import json
import sys
from typing import Any, Dict
from datetime import datetime
import uuid


class StructuredLogger:
    """
    Structured JSON logger with request_id tracking.
    """
    
    def __init__(self, name: str = "riskcanvas"):
        self.name = name
        self.logger = logging.getLogger(name)
        
        # Configure level
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        self.logger.setLevel(getattr(logging, log_level))
        
        # JSON formatter
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(self._json_formatter())
        self.logger.addHandler(handler)
        
        # Prevent duplicate logs
        self.logger.propagate = False
    
    def _json_formatter(self):
        """Create JSON log formatter"""
        class JSONFormatter(logging.Formatter):
            def format(self, record):
                log_data = {
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "level": record.levelname,
                    "logger": record.name,
                    "message": record.getMessage(),
                }
                
                # Add extra fields
                if hasattr(record, "request_id"):
                    log_data["request_id"] = record.request_id
                
                if hasattr(record, "user_id"):
                    log_data["user_id"] = record.user_id
                
                if hasattr(record, "duration_ms"):
                    log_data["duration_ms"] = record.duration_ms
                
                if record.exc_info:
                    log_data["exception"] = self.formatException(record.exc_info)
                
                return json.dumps(log_data)
        
        return JSONFormatter()
    
    def info(self, message: str, **kwargs):
        """Log info message with extra fields"""
        extra = {k: v for k, v in kwargs.items()}
        self.logger.info(message, extra=extra)
    
    def error(self, message: str, **kwargs):
        """Log error message with extra fields"""
        extra = {k: v for k, v in kwargs.items()}
        self.logger.error(message, extra=extra)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with extra fields"""
        extra = {k: v for k, v in kwargs.items()}
        self.logger.warning(message, extra=extra)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with extra fields"""
        extra = {k: v for k, v in kwargs.items()}
        self.logger.debug(message, extra=extra)


# Global logger instance
logger = StructuredLogger()


# ===== OpenTelemetry Hooks (minimal) =====


class OpenTelemetryObserver:
    """
    Minimal OpenTelemetry integration.
    Export disabled by default; enabled via OTEL_ENABLED env var.
    """
    
    def __init__(self):
        self.enabled = os.getenv("OTEL_ENABLED", "false").lower() == "true"
        self.endpoint = os.getenv("OTEL_ENDPOINT", "http://localhost:4318")
        self.service_name = os.getenv("OTEL_SERVICE_NAME", "riskcanvas-api")
        
        if self.enabled:
            self._init_otel()
    
    def _init_otel(self):
        """Initialize OpenTelemetry (placeholder for real integration)"""
        try:
            # Real integration would use:
            # from opentelemetry import trace
            # from opentelemetry.sdk.trace import TracerProvider
            # from opentelemetry.sdk.trace.export import BatchSpanProcessor
            # from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
            
            # provider = TracerProvider()
            # processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=self.endpoint))
            # provider.add_span_processor(processor)
            # trace.set_tracer_provider(provider)
            
            logger.info(f"OpenTelemetry initialized (endpoint: {self.endpoint})")
        except Exception as e:
            logger.error(f"Failed to initialize OpenTelemetry: {str(e)}")
    
    def create_span(self, name: str):
        """Create a span (placeholder)"""
        if not self.enabled:
            return None
        
        # In real implementation:
        # from opentelemetry import trace
        # tracer = trace.get_tracer(__name__)
        # return tracer.start_as_current_span(name)
        
        return None


# Global OTEL observer
otel = OpenTelemetryObserver()


# ===== Request Tracking Middleware =====


import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class RequestTrackingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to track requests with ID and duration.
    """
    
    async def dispatch(self, request: Request, call_next):
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Start timer
        start_time = time.time()
        
        # Log request
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            request_id=request_id
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log response
            logger.info(
                f"Request completed: {request.method} {request.url.path} - {response.status_code}",
                request_id=request_id,
                duration_ms=round(duration_ms, 2)
            )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
        
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                f"Request failed: {request.method} {request.url.path} - {str(e)}",
                request_id=request_id,
                duration_ms=round(duration_ms, 2)
            )
            raise
