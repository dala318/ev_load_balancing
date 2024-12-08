"""Common constants for integration."""

from enum import Enum

DOMAIN = "ev_load_balancing"


class Phases(Enum):
    """Standard numeric identifiers for phases."""

    PHASE1 = 0
    PHASE2 = 1
    PHASE3 = 2


CONF_MAINS_TYPE = "mains_type"
CONF_MAINS_DEVICE_ID = "mains_device_id"
CONF_MAINS_LIMIT = "mains_limit"
CONF_CHARGER_EXPIRES = "charger_expires"
CONF_CHARGER_TYPE = "charger_type"
CONF_CHARGER_DEVICE_ID = "charger_device_id"

NAME_SLIMMELEZER = "slimmelezer"
NAME_EASEE = "easee"
