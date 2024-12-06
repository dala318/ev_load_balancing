"""Handling Mains currents input."""

from abc import ABC, abstractmethod
from datetime import datetime

from homeassistant.core import HomeAssistant

from ..const import Phases


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

    @abstractmethod
    def get_phase(self, phase: Phases) -> MainsPhase:
        """Return phase X data."""

    @abstractmethod
    def get_rated_limit(self) -> int:
        """Return main limit per phase."""

    @abstractmethod
    def update(self) -> None:
        """Update measuremetns."""

    @abstractmethod
    def cleanup(self) -> None:
        """Cleanup event listners etc."""

    async def _async_input_changed(self, event):
        """Input entity change callback from state change event."""
        # _LOGGER.debug("Sensor change event from HASS: %s", event)
        await self._update_callback()
