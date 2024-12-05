"""Handles the coordination between mains and charger."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry, Debouncer
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .chargers import Charger, ChargingState
from .chargers.easee import ChargerEasee
from .mains import Mains
from .mains.slimmelezer import MainsSlimmelezer

_LOGGER = logging.getLogger(__name__)


class PhasePair:
    """Data analyzer per one phase."""


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

        actuals = []
        actuals.append(self._mains.current_phase1())
        actuals.append(self._mains.current_phase2())
        actuals.append(self._mains.current_phase3())
        # actual_phase1 = self._mains.current_phase1()
        # actual_phase2 = self._mains.current_phase2()
        # actual_phase3 = self._mains.current_phase3()

        charging_state = self._charger.charging_state()
        limits = []
        limits.append(self._charger.limit_phase1())
        limits.append(self._charger.limit_phase2())
        limits.append(self._charger.limit_phase3())
        # limit_phase1 = self._charger.limit_phase1()
        # limit_phase2 = self._charger.limit_phase2()
        # limit_phase3 = self._charger.limit_phase3()
        limit_circuit = self._charger.limit_circuit()

        mapping = {0: 1, 1: 2, 2: 0}

        if charging_state == ChargingState.OFF:
            _LOGGER.debug("Skipping update since no charging active or pending")
            return

        new_limits = []
        for a_index, l_index in mapping.items():
            if actuals[a_index] is None or limits[l_index] is None:
                _LOGGER.debug("Skipping update since None value found")
                return
            spare = self._max_load - actuals[a_index]
            new = min(limits[l_index] + spare, self._max_load, limit_circuit)
            # new = min(new, limit_circuit)
            new_limits.append(new)

        pass
