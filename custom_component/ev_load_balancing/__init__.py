"""Main package for coordinator."""

from __future__ import annotations

import logging

from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry, Debouncer
from homeassistant.const import CONF_API_KEY, CONF_NAME, CONF_URL, Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from . import chargers, coordinator, mains
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# PLATFORMS = [Platform.BINARY_SENSOR, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up this integration using UI."""
    config_entry.async_on_unload(config_entry.add_update_listener(async_reload_entry))

    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}

    if config_entry.entry_id not in hass.data[DOMAIN]:
        coordinator = EvLoadBalancingCoordinator(hass, config_entry)
        hass.data[DOMAIN][config_entry.entry_id] = coordinator

    # if config_entry is not None:
    #     if config_entry.source == SOURCE_IMPORT:
    #         hass.async_create_task(
    #             hass.config_entries.async_remove(config_entry.entry_id)
    #         )
    #         return False

    await hass.data[DOMAIN][config_entry.entry_id].async_config_entry_first_refresh()

    # await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unloading a config_flow entry."""
    # unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    unload_ok = True
    if unload_ok:
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        coordinator.cleanup()
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Reload the config entry."""
    await async_unload_entry(hass, config_entry)
    await async_setup_entry(hass, config_entry)


class EvLoadBalancingCoordinator(DataUpdateCoordinator):
    """Coordinator base class."""

    _mains: mains.Mains
    _charger: chargers.Charger

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
        self._mains = mains.MainsSlimmelezer(
            hass, self.async_request_refresh, "6b332da8a66c649c42f284a079a8bcaa"
        )
        # self.async_add_listener()

        # Charger
        self._charger = chargers.ChargerEasee(
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

        charging_active = self._charger.is_charging_active()
        limits = []
        limits.append(self._charger.limit_phase1())
        limits.append(self._charger.limit_phase2())
        limits.append(self._charger.limit_phase3())
        # limit_phase1 = self._charger.limit_phase1()
        # limit_phase2 = self._charger.limit_phase2()
        # limit_phase3 = self._charger.limit_phase3()
        limit_circuit = self._charger.limit_circuit()

        mapping = {0: 1, 1: 2, 2: 0}

        new_limits = []
        for a, l in mapping.items():
            spare = self._max_load - actuals[a]
            new = min(limits[l] + spare, self._max_load, limit_circuit)
            # new = min(new, limit_circuit)
            new_limits.append(new)

        pass
