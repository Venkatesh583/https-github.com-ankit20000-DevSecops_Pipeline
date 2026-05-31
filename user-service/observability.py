import json
import logging
import os
import time
import uuid
from datetime import datetime

from flask import Flask, g, request
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "service": getattr(record, "service", os.getenv("OTEL_SERVICE_NAME", "user-service")),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        for field in [
            "request_id",
            "trace_id",
            "span_id",
            "path",
            "method",
            "status_code",
            "duration_ms",
            "remote_url",
            "remote_method",
            "error",
        ]:
            value = getattr(record, field, None)
            if value is not None:
                log_entry[field] = value

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


def setup_logging(service_name):
    logger = logging.getLogger("healthcare")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()
    logger.propagate = False

    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)

    for noisy_logger in ["werkzeug", "urllib3"]:
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)

    return logger


def configure_tracing(app: Flask, service_name: str):
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4318")
    if endpoint.endswith("/v1/traces"):
        exporter_endpoint = endpoint
    else:
        exporter_endpoint = f"{endpoint.rstrip('/')}/v1/traces"

    resource = Resource.create({
        "service.name": service_name,
        "service.namespace": "healthcare",
    })

    provider = TracerProvider(resource=resource)
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=exporter_endpoint)))
    trace.set_tracer_provider(provider)

    FlaskInstrumentor().instrument_app(app)
    RequestsInstrumentor().instrument()
    try:
        SQLAlchemyInstrumentor().instrument()
    except Exception:
        pass


def configure_observability(app: Flask, service_name: str):
    logger = setup_logging(service_name)
    configure_tracing(app, service_name)

    @app.before_request
    def before_request():
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        g.request_id = request_id
        g.start_time = time.monotonic()
        log_event(
            logging.INFO,
            "request_started",
            request_id=request_id,
            path=request.path,
            method=request.method,
            service=service_name,
            client_ip=request.remote_addr,
            user_agent=request.user_agent.string if request.user_agent else None,
        )

    @app.after_request
    def after_request(response):
        duration_ms = round((time.monotonic() - g.start_time) * 1000, 2)
        response.headers["X-Request-ID"] = getattr(g, "request_id", None)
        trace_id = None
        span_context = trace.get_current_span().get_span_context()
        if span_context.is_valid:
            trace_id = format(span_context.trace_id, "032x")
            response.headers["X-Trace-Id"] = trace_id

        log_event(
            logging.INFO,
            "request_completed",
            request_id=getattr(g, "request_id", None),
            path=request.path,
            method=request.method,
            status_code=response.status_code,
            duration_ms=duration_ms,
            service=service_name,
        )
        return response

    @app.errorhandler(404)
    def handle_not_found(error):
        duration_ms = round((time.monotonic() - getattr(g, "start_time", time.monotonic())) * 1000, 2)
        log_event(
            logging.WARNING,
            "resource_not_found",
            request_id=getattr(g, "request_id", None),
            path=request.path,
            method=request.method,
            status_code=404,
            duration_ms=duration_ms,
            service=service_name,
            error=str(error),
        )
        return {
            "error": "not_found",
            "message": "Resource not found",
            "request_id": getattr(g, "request_id", None),
        }, 404

    @app.errorhandler(Exception)
    def handle_exception(error):
        duration_ms = round((time.monotonic() - getattr(g, "start_time", time.monotonic())) * 1000, 2)
        log_event(
            logging.ERROR,
            "unhandled_exception",
            request_id=getattr(g, "request_id", None),
            path=request.path,
            method=request.method,
            status_code=500,
            duration_ms=duration_ms,
            service=service_name,
            error=str(error),
        )
        logger.exception("Unhandled exception")
        return {
            "error": "internal_server_error",
            "message": "Internal server error",
            "request_id": getattr(g, "request_id", None),
        }, 500

    app.logger = logger
    return logger


def log_event(level, message, **extra):
    logger = logging.getLogger("healthcare")
    span = trace.get_current_span()
    span_context = span.get_span_context()

    if span_context.is_valid:
        extra.setdefault("trace_id", format(span_context.trace_id, "032x"))
        extra.setdefault("span_id", format(span_context.span_id, "016x"))

    logger.log(level, message, extra=extra)
