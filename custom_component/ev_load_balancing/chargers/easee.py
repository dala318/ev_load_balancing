"""Handling Easee Charger."""

import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.template import device_entities

from ..const import Phases
from ..helpers.entity_value import get_sensor_entity_attribute_value
from . import Charger, ChargerPhase, ChargingState

_LOGGER = logging.getLogger(__name__)


class ChargerPhaseEasee(ChargerPhase):
    """A data class for a charger phase."""

    def __init__(self, hass: HomeAssistant, entity_id: str, attribute: str) -> None:
        """Initialize object."""
        self._hass = hass
        self._entity = entity_id
        self._attribute = attribute

    def current_limit(self) -> float:
        """Get set current limit on phase."""
        return get_sensor_entity_attribute_value(
            self._hass,
            _LOGGER,
            self._entity,
            self._attribute,
        )


class ChargerEasee(Charger):
    """Slimmelezer mains extractor."""

    _state_change_listeners = []

    def __init__(self, hass: HomeAssistant, update_callback, device_id: str) -> None:
        """Initilalize Slimmelezer extractor."""
        super().__init__(hass, update_callback)
        self._id = device_id

        entities = device_entities(hass, device_id)

        self._ent_status = [e for e in entities if e.endswith("_status")][0]
        self._state_change_listeners.append(
            async_track_state_change_event(
                self._hass,
                [self._ent_status],
                self._async_input_changed,
            )
        )

        self._ent_circuit_limit = [
            e for e in entities if e.endswith("_dynamic_circuit_limit")
        ][0]
        self._state_change_listeners.append(
            async_track_state_change_event(
                self._hass,
                [self._ent_circuit_limit],
                self._async_input_changed,
            )
        )

        self._phase1 = ChargerPhaseEasee(
            self._hass, self._ent_circuit_limit, "state_dynamicCircuitCurrentP1"
        )
        self._phase2 = ChargerPhaseEasee(
            self._hass, self._ent_circuit_limit, "state_dynamicCircuitCurrentP2"
        )
        self._phase3 = ChargerPhaseEasee(
            self._hass, self._ent_circuit_limit, "state_dynamicCircuitCurrentP3"
        )

    def set_limits(self, phase1: float, phase2: float, phase3: float) -> bool:
        """Set charger limits."""
        _LOGGER.debug(
            "Setting limits: phase 1 %f, phase 2 %f, phase 3 %f", phase1, phase2, phase3
        )
        return True

    def cleanup(self):
        """Cleanup by removing event listeners."""
        # for listner in self._state_change_listeners:
        #     listner()

    @property
    def charging_state(self) -> ChargingState:
        """Return if charging state."""
        if self._hass.states.get(self._ent_status).state in ["charging"]:
            return ChargingState.CHARGING
        if self._hass.states.get(self._ent_status).state in ["awaiting_start"]:
            return ChargingState.PENDING
        return ChargingState.OFF

    def get_phase(self, phase: Phases) -> ChargerPhase:
        """Return phase X data."""
        if phase == Phases.PHASE1:
            return self._phase1
        if phase == Phases.PHASE2:
            return self._phase2
        if phase == Phases.PHASE3:
            return self._phase3
        return None

    def get_rated_limit(self) -> int:
        """Return overall limit per phase on charger circuit."""
        limit = get_sensor_entity_attribute_value(
            self._hass, _LOGGER, self._ent_circuit_limit, "circuit_ratedCurrent"
        )
        if limit is not None:
            limit = int(limit)
            _LOGGER.debug("Returning rated limit %d for charger circuit", limit)
        return limit
