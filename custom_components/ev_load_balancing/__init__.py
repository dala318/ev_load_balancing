"""Main package for coordinator."""

from __future__ import annotations

import logging

# from homeassistant.const import CONF_API_KEY, CONF_NAME, CONF_URL, Platform
# from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
# from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import EvLoadBalancingCoordinator

_LOGGER = logging.getLogger(__name__)

# PLATFORMS = [Platform.BINARY_SENSOR, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up this integration using UI."""
    config_entry.async_on_unload(config_entry.add_update_listener(async_reload_entry))

    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}

    if config_entry.entry_id not in hass.data[DOMAIN]:
        coordinator = EvLoadBalancingCoordinator(hass, config_entry)
        await coordinator.async_config_entry_first_refresh()

        hass.data[DOMAIN][config_entry.entry_id] = coordinator

    # await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unloading a config_flow entry."""
    # unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    unload_ok = True
    if unload_ok:
        coordinator: EvLoadBalancingCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
        coordinator.cleanup()
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Reload the config entry."""
    await async_unload_entry(hass, config_entry)
    await async_setup_entry(hass, config_entry)