"""Handling Chargers."""

from abc import ABC, abstractmethod
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.template import device_entities

# from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class ChargerPhase(ABC):
    """A data class for a charger phase."""

    def __init__(self) -> None:
        """Initialize object."""
        pass

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
    def is_charging_active(self) -> bool:
        """Return if charging is active."""

    @abstractmethod
    def cleanup(self) -> None:
        """Cleanup event listners etc."""

    @abstractmethod
    def limit_phase1(self) -> float:
        """Return limit of phase 1."""

    @abstractmethod
    def limit_phase2(self) -> float:
        """Return limit of phase 2."""

    @abstractmethod
    def limit_phase3(self) -> float:
        """Return limit of phase 3."""

    @abstractmethod
    def limit_circuit(self) -> float:
        """Return overall limit per phase on charger circuit."""

    async def _async_input_changed(self, event):
        """Input entity change callback from state change event."""
        _LOGGER.debug("Sensor change event from HASS: %s", event)
        await self._update_callback()

    def _get_sensor_entity_attribute_value(
        self, entity_id: str, attribute: str
    ) -> float | None:
        """Get value of generic entity parameter."""
        if entity_id:
            try:
                entity = self._hass.states.get(entity_id)
                # return SensorValue(float(entity.state), entity.last_reported)
                return float(entity.attributes.get(attribute))
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

    def set_limits(self, phase1: float, phase2: float, phase3: float) -> bool:
        """Set charger limits."""
        _LOGGER.debug(
            "Setting limits: phase 1 %f, phase 2 %f, phase 3 %f", phase1, phase2, phase3
        )
        return True

    def cleanup(self):
        """Cleanup by removing event listeners."""
        for listner in self._state_change_listeners:
            listner()

    def is_charging_active(self) -> bool:
        """Return if charging is active."""
        return self._hass.states.get(self._ent_status).state == "charging"

    def limit_phase1(self) -> float:
        """Get current limit of phase 1."""
        limit = self._get_sensor_entity_attribute_value(
            self._ent_circuit_limit, "state_dynamicCircuitCurrentP1"
        )
        _LOGGER.debug("Returning limit %f for phase 1", limit)
        return limit

    def limit_phase2(self) -> float:
        """Get current limit of phase 2."""
        limit = self._get_sensor_entity_attribute_value(
            self._ent_circuit_limit, "state_dynamicCircuitCurrentP2"
        )
        _LOGGER.debug("Returning limit %f for phase 2", limit)
        return limit

    def limit_phase3(self) -> float:
        """Get current limit of phase 3."""
        limit = self._get_sensor_entity_attribute_value(
            self._ent_circuit_limit, "state_dynamicCircuitCurrentP3"
        )
        _LOGGER.debug("Returning limit %f for phase 3", limit)
        return limit

    def limit_circuit(self) -> float:
        """Return overall limit per phase on charger circuit."""
        limit = self._get_sensor_entity_attribute_value(
            self._ent_circuit_limit, "circuit_ratedCurrent"
        )
        _LOGGER.debug("Returning limit %f for phase 3", limit)
        return limit
