"""Handling Mains currents input."""

from abc import ABC, abstractmethod
from datetime import UTC, datetime, timedelta
import logging

from homeassistant.core import HomeAssistant, dataclass
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.template import device_entities

# from .const import DOMAIN

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


class MainsSlimmelezer(Mains):
    """Slimmelezer mains extractor."""

    _state_change_listeners = []
    _variance_min_num = 10
    _variance_max_age = timedelta(minutes=2)

    def __init__(self, hass: HomeAssistant, update_callback, device_id: str) -> None:
        """Initilalize Slimmelezer extractor."""
        super().__init__(hass, update_callback)
        self._id = device_id

        entities = device_entities(hass, device_id)

        self._ent_phase1 = [e for e in entities if "_current" in e and e.endswith("1")][
            0
        ]
        self._state_change_listeners.append(
            async_track_state_change_event(
                self._hass,
                [self._ent_phase1],
                self._async_input_changed,
                # self._async_input_changed_local,
            )
        )

        self._ent_phase2 = [e for e in entities if "_current" in e and e.endswith("2")][
            0
        ]
        self._state_change_listeners.append(
            async_track_state_change_event(
                self._hass,
                [self._ent_phase2],
                self._async_input_changed,
                # self._async_input_changed_local,
            )
        )

        self._ent_phase3 = [e for e in entities if "_current" in e and e.endswith("3")][
            0
        ]
        self._state_change_listeners.append(
            async_track_state_change_event(
                self._hass,
                [self._ent_phase3],
                self._async_input_changed,
                # self._async_input_changed_local,
            )
        )

    # async def _async_input_changed_local(self, event):
    #     """Input entity change callback from state change event."""
    #     # _LOGGER.debug("Sensor change event from HASS: %s", event)
    #     new_state = event
    #     await super()._update_callback()

    def current_phase1(self) -> float | None:
        """Get phase 1 current."""
        now = datetime.now(UTC)
        measurement = self._get_sensor_entity_value(self._ent_phase1)
        if not measurement:
            _LOGGER.warning("Returning None for phase 1")
            return None
        if measurement.timestamp not in self._history_phase1:
            self._history_phase1[measurement.timestamp] = measurement.value

            # Find and drop old values if enough in dict
            # ToDo: This is still work-in-progress since the datetime is not updated if same value
            # Wait to get it working before copying to the remaining phases
            drop_keys = []
            keep_count = 0
            for k in sorted(self._history_phase1.keys(), reverse=True):
                if (
                    keep_count < self._variance_min_num
                    or k > now - self._variance_max_age
                ):
                    keep_count += 1
                else:
                    drop_keys.append(k)
            for k in drop_keys:
                self._history_phase1.pop(k)
                _LOGGER.debug("Dropping measurement with key %s", k)
        _LOGGER.debug("Returning current %f for phase 1", measurement.value)
        return measurement.value

    def current_phase2(self) -> float | None:
        """Get phase 2 current."""
        measurement = self._get_sensor_entity_value(self._ent_phase2)
        if not measurement:
            _LOGGER.warning("Returning None for phase 2")
            return None
        _LOGGER.debug("Returning current %f for phase 2", measurement.value)
        return measurement.value

    def current_phase3(self) -> float | None:
        """Get phase 3 current."""
        measurement = self._get_sensor_entity_value(self._ent_phase3)
        if not measurement:
            _LOGGER.warning("Returning None for phase 3")
            return None
        _LOGGER.debug("Returning current %f for phase 3", measurement.value)
        return measurement.value

    def cleanup(self):
        """Cleanup by removing event listeners."""
        for listner in self._state_change_listeners:
            listner()
