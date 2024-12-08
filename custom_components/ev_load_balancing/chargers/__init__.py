"""Handling Chargers."""

from abc import ABC, abstractmethod
from enum import Enum

from homeassistant.core import HomeAssistant

from ..const import Phases


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
    async def async_set_limits(
        self, phase1: float, phase2: float, phase3: float
    ) -> bool:
        """Set charger limits."""

    @abstractmethod
    def update(self) -> None:
        """Update measuremetns."""

    @abstractmethod
    def cleanup(self) -> None:
        """Cleanup event listners etc."""

    @property
    @abstractmethod
    def charging_state(self) -> ChargingState:
        """Return charging state."""

    @abstractmethod
    def get_phase(self, phase: Phases) -> ChargerPhase:
        """Return phase X data."""

    @abstractmethod
    def get_rated_limit(self) -> int:
        """Return charger limit per phase."""

    @property
    @abstractmethod
    def device_id(self) -> str:
        """Device id."""

    async def _async_input_changed(self, event):
        """Input entity change callback from state change event."""
        # _LOGGER.debug("Sensor change event from HASS: %s", event)
        await self._update_callback()
