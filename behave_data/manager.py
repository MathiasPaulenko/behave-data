"""Minimal DataManager stub for MVP.

The full implementation comes in Fase 3.3.
For now, it just stores the config.
"""

from __future__ import annotations

from behave_data.config import Config


class DataManager:
    """Minimal data manager that stores configuration.

    Attributes:
        config: The behave-data configuration.
    """

    def __init__(self, config: Config) -> None:
        self.config = config
