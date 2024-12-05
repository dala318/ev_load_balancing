"""Handling Slimmelezer mains currents input."""

from datetime import UTC, datetime, timedelta
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.template import device_entities

from ..helpers.entity_value import get_sensor_entity_value
from . import Mains, MainsPhase

_LOGGER = logging.getLogger(__name__)


class MainsPhaseSlimmelezer(MainsPhase):
    """A data class for a mains phase."""

    def __init__(self, hass: HomeAssistant, entity_id: str) -> None:
        """Initialize object."""
        self._hass = hass
        self._entity = entity_id

    def actual_current(self) -> float:
        """Get actual current on phase."""
        return get_sensor_entity_value(
            self._hass,
            _LOGGER,
            self._entity,
        )

    def stddev_current(self) -> float:
        """Get standard deviation of current on phase."""
        return 0


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
        used_entities = []

        entity_phase1 = [e for e in entities if "_current" in e and e.endswith("1")][0]
        self._phase1 = MainsPhaseSlimmelezer(self._hass, entity_phase1)
        used_entities.append(entity_phase1)

        entity_phase2 = [e for e in entities if "_current" in e and e.endswith("2")][0]
        self._phase2 = MainsPhaseSlimmelezer(self._hass, entity_phase2)
        used_entities.append(entity_phase2)

        entity_phase3 = [e for e in entities if "_current" in e and e.endswith("3")][0]
        self._phase3 = MainsPhaseSlimmelezer(self._hass, entity_phase3)
        used_entities.append(entity_phase3)

        self._state_change_listeners.append(
            async_track_state_change_event(
                self._hass,
                used_entities,
                self._async_input_changed,
                # self._async_input_changed_local,
            )
        )

    @property
    def phase1(self) -> MainsPhase:
        """Get phase 1 data."""
        return self._phase1

    # def current_phase1(self) -> float | None:
    #     """Get phase 1 current."""
    #     now = datetime.now(UTC)
    #     measurement = self._get_sensor_entity_value(self._ent_phase1)
    #     if not measurement:
    #         _LOGGER.warning("Returning None for phase 1")
    #         return None
    #     if measurement.timestamp not in self._history_phase1:
    #         self._history_phase1[measurement.timestamp] = measurement.value

    #         # Find and drop old values if enough in dict
    #         # ToDo: This is still work-in-progress since the datetime is not updated if same value
    #         # Wait to get it working before copying to the remaining phases
    #         drop_keys = []
    #         keep_count = 0
    #         for k in sorted(self._history_phase1.keys(), reverse=True):
    #             if (
    #                 keep_count < self._variance_min_num
    #                 or k > now - self._variance_max_age
    #             ):
    #                 keep_count += 1
    #             else:
    #                 drop_keys.append(k)
    #         for k in drop_keys:
    #             self._history_phase1.pop(k)
    #             _LOGGER.debug("Dropping measurement with key %s", k)
    #     _LOGGER.debug("Returning current %f for phase 1", measurement.value)
    #     return measurement.value

    @property
    def phase2(self) -> MainsPhase:
        """Get phase 2 data."""
        return self._phase2

    @property
    def phase3(self) -> MainsPhase:
        """Get phase 3 data."""
        return self._phase3

    def cleanup(self):
        """Cleanup by removing event listeners."""
        for listner in self._state_change_listeners:
            listner()
