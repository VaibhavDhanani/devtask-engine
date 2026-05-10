import logging
import os
import sys

import structlog

from app.core.config import settings

_IN_PYCHARM = bool(os.environ.get("PYCHARM_HOSTED"))
_LOG_STREAM = sys.stdout if _IN_PYCHARM else sys.stderr
_USE_COLOR = _LOG_STREAM.isatty() or _IN_PYCHARM

_LEVEL_COLORS = {
    "debug": "\033[37m",
    "info": "\033[32m",
    "warning": "\033[33m",
    "error": "\033[31m",
    "critical": "\033[1;31m",
}
_RESET = "\033[0m"


class _ColorByLevelRenderer:
    def __init__(self, use_color: bool) -> None:
        self._inner = structlog.dev.ConsoleRenderer(colors=False)
        self._use_color = use_color

    def __call__(self, logger, name, event_dict):
        level = event_dict.get("level", "info")
        rendered = self._inner(logger, name, event_dict)
        if not self._use_color:
            return rendered
        color = _LEVEL_COLORS.get(level, "")
        return f"{color}{rendered}{_RESET}" if color else rendered


def configure_logging() -> None:
    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        timestamper,
    ]

    if settings.log_json:
        renderer: structlog.types.Processor = structlog.processors.JSONRenderer()
    else:
        renderer = _ColorByLevelRenderer(use_color=_USE_COLOR)

    structlog.configure(
        processors=[*shared_processors, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.log_level)
        ),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        format="%(message)s",
        stream=_LOG_STREAM,
        level=getattr(logging, settings.log_level),
    )

    for noisy in ("uvicorn.access", "sqlalchemy.engine"):
        logging.getLogger(noisy).setLevel(
            logging.WARNING if not settings.debug else logging.INFO
        )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)
