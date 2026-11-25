"""Logging setup. Logs never include request bodies, chat text or precise locations."""

import logging


def configure_logging(level: str) -> None:
    """Configure root logging once with a compact format."""
    logging.basicConfig(
        level=level.upper(),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
