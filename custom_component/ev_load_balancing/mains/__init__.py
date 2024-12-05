"""Handling Mains currents input."""

from abc import ABC, abstractmethod
from datetime import datetime
import logging

from homeassistant.core import HomeAssistant, dataclass

_LOGGER = logging.getLogger(__name__)


@dataclass
class SensorValue:
    """Data collector class for sensor measurement."""

    value: float
    timestamp: datetime

    def __init__(self, value: float, timestamp: datetime) -> None:
        """Class initilaizer."""
        self.value = value
        self.timestamp = timestamp


class MainsPhase(ABC):
    """A data class for a mains phase."""

    # def __init__(self) -> None:
    #     """Initialize object."""

    @abstractmethod
    def actual_current(self) -> float:
        """Get actual current on phase."""

    @abstractmethod
    def stddev_current(self) -> float:
        """Get standard deviation of current on phase."""


class Mains(ABC):
    """Base class for Mains extractor."""

    _history_phase1: dict[datetime, float] = {}
    _history_phase2: dict[datetime, float] = {}
    _history_phase3: dict[datetime, float] = {}

    def __init__(self, hass: HomeAssistant, update_callback) -> None:
        """Initialize base class."""
        self._hass = hass
        self._update_callback = update_callback

    @property
    @abstractmethod
    def phase1(self) -> MainsPhase:
        """Return phase 1 data."""

    @property
    @abstractmethod
    def phase2(self) -> MainsPhase:
        """Return phase 2 data."""

    @property
    @abstractmethod
    def phase3(self) -> MainsPhase:
        """Return phase 3 data."""

    @abstractmethod
    def cleanup(self) -> None:
        """Cleanup event listners etc."""

    async def _async_input_changed(self, event):
        """Input entity change callback from state change event."""
        # _LOGGER.debug("Sensor change event from HASS: %s", event)
        await self._update_callback()
