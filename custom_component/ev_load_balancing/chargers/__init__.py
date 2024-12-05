"""Handling Chargers."""

from abc import ABC, abstractmethod
import logging

from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


# class ChargerPhase(ABC):
#     """A data class for a charger phase."""

#     def __init__(self) -> None:
#         """Initialize object."""

#     def current_limit(self) -> float:
#         """Get set current limit on phase."""
#         return 1.0


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
