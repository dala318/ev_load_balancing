"""Handles the coordination between mains and charger."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry, Debouncer
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .chargers import Charger, ChargerPhase, ChargingState
from .chargers.easee import ChargerEasee
from .mains import Mains, MainsPhase
from .mains.slimmelezer import MainsSlimmelezer

_LOGGER = logging.getLogger(__name__)


class PhasePair:
    """Data analyzer per one phase."""

    def __init__(self, mains: MainsPhase, charger: ChargerPhase) -> None:
        """Pair of Charger and Mains phases."""
        self._mains = mains
        self._charger = charger

    def get_new_limit(self) -> float | None:
        main_actual = self._mains.actual_current()
        main_limit = 20
        charger_limit = self._charger.current_limit()
        charger_rating = 16
        if main_actual is None or charger_limit is None:
            _LOGGER.debug("Skipping update since None value found")
            return None
        spare = main_limit - main_actual
        return min(charger_limit + spare, charger_rating, main_limit)


class EvLoadBalancingCoordinator(DataUpdateCoordinator):
    """Coordinator base class."""

    _mains: Mains
    _charger: Charger

    _max_load = 19.0

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize my coordinator."""
        self._hass = hass
        super().__init__(
            hass,
            _LOGGER,
            name=config_entry.data.get(CONF_NAME),
            # update_interval=timedelta(seconds=20),
            update_method=self._async_update_method,
            request_refresh_debouncer=Debouncer(
                hass,
                _LOGGER,
                cooldown=1,
                immediate=False,
                # function=self.async_refresh,
            ),
            # always_update=True,
        )

        # Mains currents
        self._mains = MainsSlimmelezer(
            hass, self.async_request_refresh, "6b332da8a66c649c42f284a079a8bcaa"
        )

        # Charger
        self._charger = ChargerEasee(
            hass, self.async_request_refresh, "308b36c34ff3cd9766f693be289a8f3b"
        )

        # mapping = {0: 1, 1: 2, 2: 0}
        self._pairs = [
            PhasePair(self._mains.phase1, self._charger.phase1),
            PhasePair(self._mains.phase3, self._charger.phase2),
            PhasePair(self._mains.phase3, self._charger.phase2),
        ]

    def cleanup(self) -> None:
        """Cleanup any pending event listers etc."""
        self._mains.cleanup()
        self._charger.cleanup()

    def get_device_info(self) -> DeviceInfo:
        """Get device info to group entities."""
        return DeviceInfo(
            name=self.name,
            # manufacturer="LoadBalancing",
            entry_type=DeviceEntryType.SERVICE,
        )

    async def async_config_entry_first_refresh(self):
        """Refresh data on setup."""
        pass

    async def _async_update_method(self):
        """Update call function."""
        _LOGGER.info("Updating service")

        if self._charger.charging_state == ChargingState.OFF:
            _LOGGER.debug("Skipping update since no charging active or pending")
            return

        for pair in self._pairs:
            new_limit = pair.get_new_limit()
            _LOGGER.debug("Calculated new circuit limit %f", new_limit)

        pass
