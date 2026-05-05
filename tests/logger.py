"""Structured logger."""

import os
import structlog

structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer()
        if os.getenv("SUP_ENV") == "dev"
        else structlog.processors.JSONRenderer(),
    ],
)

log = structlog.get_logger()
