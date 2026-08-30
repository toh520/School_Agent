"""Structured console logging with conservative secret masking."""

import logging
import re

_SECRET_ASSIGNMENT = re.compile(
    r"(?i)(password|passwd|token|secret|api[_-]?key|authorization)(\s*[=:]\s*)([^\s,;]+)"
)


def mask_sensitive_text(message: str) -> str:
    """Mask common credential assignments without logging their values."""

    return _SECRET_ASSIGNMENT.sub(r"\1\2***", message)


class SensitiveDataFilter(logging.Filter):
    """Redact formatted messages before the console handler emits them."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = mask_sensitive_text(record.getMessage())
        record.args = ()
        return True


def configure_logging() -> None:
    """Install the M01 console format once for the Agent service."""

    handler = logging.StreamHandler()
    handler.addFilter(SensitiveDataFilter())
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s level=%(levelname)s service=agent-service "
            'logger=%(name)s message="%(message)s"'
        )
    )
    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(logging.INFO)
