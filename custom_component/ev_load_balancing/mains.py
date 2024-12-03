"""Handling Mains currents input."""

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable, Coroutine
from datetime import datetime, timedelta
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.template import device_entities

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class Mains(ABC):
    """Base class for Mains extractor."""

    _last_event_timestamp: datetime = None

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize base class."""
        self._hass = hass

    @abstractmethod
    def current_phase1(self) -> float | None:
        """Get phase 1 current."""

    @abstractmethod
    def cleanup(self) -> None:
        """Cleanup event listners etc."""

    async def _async_input_changed(self, event):
        """Input entity change callback from state change event."""
        if not self._last_event_timestamp or (
            event.time_fired - self._last_event_timestamp
        ) > timedelta(seconds=1):
            self._last_event_timestamp = event.time_fired
            _LOGGER.debug("Sensor change event from HASS: %s", event)
            # self.update()

    def _get_sensor_entity_value(self, entity_id: str) -> float | None:
        """Get value of generic entity parameter."""
        if entity_id:
            try:
                entity = self._hass.states.get(entity_id)
                state = entity.state
                value = float(state)
                # if integer:
                #     return int(value)
                return value  # noqa: RET504, TRY300
            except (TypeError, ValueError):
                _LOGGER.warning(
                    'Could not convert value "%s" of entity %s to expected format',
                    state,
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

    def __init__(self, hass: HomeAssistant, device_id: str) -> None:
        """Initilalize Slimmelezer extractor."""
        super().__init__(hass)
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
            )
        )

        pass

    def current_phase1(self) -> float | None:
        """Get phase 1 current."""
        current = self._get_sensor_entity_value(self._ent_phase1)
        _LOGGER.debug("Returning current %f for phase 1", current)
        return current

    def cleanup(self):
        """Cleanup by removing event listeners."""
        for listner in self._state_change_listeners:
            listner()
