"""Handling Chargers."""

from abc import ABC, abstractmethod
import logging

from homeassistant.config_entries import Enum
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


class ChargingState(Enum):
    """State of charger."""

    OFF = 0
    PENDING = 1
    CHARGING = 2


class ChargerPhase(ABC):
    """A data class for a charger phase."""

    # def __init__(self) -> None:
    #     """Initialize object."""

    @abstractmethod
    def current_limit(self) -> float:
        """Get set current limit on phase."""


class Charger(ABC):
    """Base class for Charger robot."""

    def __init__(self, hass: HomeAssistant, update_callback) -> None:
        """Initialize base class."""
        self._hass = hass
        self._update_callback = update_callback

    @abstractmethod
    def set_limits(self, phase1: float, phase2: float, phase3: float) -> bool:
        """Set charger limits."""

    @abstractmethod
    def cleanup(self) -> None:
        """Cleanup event listners etc."""

    @property
    @abstractmethod
    def charging_state(self) -> ChargingState:
        """Return charging state."""

    @property
    @abstractmethod
    def phase1(self) -> ChargerPhase:
        """Return phase 1 data."""

    @property
    @abstractmethod
    def phase2(self) -> ChargerPhase:
        """Return phase 2 data."""

    @property
    @abstractmethod
    def phase3(self) -> ChargerPhase:
        """Return phase 3 data."""

    @property
    @abstractmethod
    def limit_circuit(self) -> float:
        """Return overall limit per phase on charger circuit."""

    async def _async_input_changed(self, event):
        """Input entity change callback from state change event."""
        _LOGGER.debug("Sensor change event from HASS: %s", event)
        await self._update_callback()
