"""Common constants for integration."""

from enum import Enum

DOMAIN = "ev_load_balancing"


class Phases(Enum):
    """Standard numeric identifiers for phases."""

    PHASE1 = 0
    PHASE2 = 1
    PHASE3 = 2
