"""Handling Chargers."""

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable, Coroutine
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.template import device_entities

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class Charger(ABC):
    """Base class for Charger robot."""

    # def __init__(self) -> None:
    #     """Initialize base class."""
    #     pass

    @abstractmethod
    def set_limits(self, phase1: float, phase2: float, phase3: float) -> bool:
        """Set charger limits."""

    @abstractmethod
    def cleanup(self) -> None:
        """Cleanup event listners etc."""

    async def _async_input_changed(self, event):
        """Input entity change callback from state change event."""
        # new_state = event.data.get("new_state")
        _LOGGER.debug("Sensor change event from HASS: %s", event)
        # self.update()


class ChargerEasee(Charger):
    """Slimmelezer mains extractor."""

    _state_change_listeners = []

    def __init__(self, hass: HomeAssistant, device_id: str) -> None:
        """Initilalize Slimmelezer extractor."""
        self._hass = hass
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
        # Circuit ID                      292,000
        # Circuit circuitPanelId          1
        # Circuit panelName               1
        # Circuit ratedCurrent            16
        # State dynamicCircuitCurrentP1   16
        # State dynamicCircuitCurrentP2   16
        # State dynamicCircuitCurrentP3   16

        pass

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
