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
    def current_phase1(self) -> float | None:
        """Get phase 1 current."""

    @abstractmethod
    def current_phase2(self) -> float | None:
        """Get phase 2 current."""

    @abstractmethod
    def current_phase3(self) -> float | None:
        """Get phase 3 current."""

    @abstractmethod
    def cleanup(self) -> None:
        """Cleanup event listners etc."""

    async def _async_input_changed(self, event):
        """Input entity change callback from state change event."""
        # _LOGGER.debug("Sensor change event from HASS: %s", event)
        await self._update_callback()

    def _get_sensor_entity_value(self, entity_id: str) -> SensorValue | None:
        """Get value of generic entity parameter."""
        if entity_id:
            try:
                entity = self._hass.states.get(entity_id)
                return SensorValue(float(entity.state), entity.last_reported)
                # return float(entity.state)
            except (TypeError, ValueError):
                _LOGGER.warning(
                    'Could not convert value "%s" of entity %s to expected format',
                    entity.state,
                    entity_id,
                )
            except Exception as e:  # noqa: BLE001
                _LOGGER.error(
                    'Unknown error when reading and converting "%s": %s',
                    entity_id,
                    e,
                )
        else:
            _LOGGER.debug("No entity defined")
        return None
