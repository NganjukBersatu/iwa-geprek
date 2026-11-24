"""Where the service's own log lines go: every logger under "cafe" writes to standard output, which Railway shows and keeps."""
import logging
import sys

ROOT = "cafe"
FORMAT = "%(levelname)s %(name)s: %(message)s"


def install() -> None:
    logger = logging.getLogger(ROOT)
    if logger.handlers:
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(FORMAT))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
