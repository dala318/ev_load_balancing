"""Sensor definitions."""

from __future__ import annotations

import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_UNKNOWN
from homeassistant.core import HomeAssistant

from . import EvLoadBalancingCoordinator
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities
):
    """Create state sensor entities for platform."""

    coordinator: EvLoadBalancingCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    entities = []

    entities.append(
        LastUpdateSensor(
            coordinator,
            entity_description=SensorEntityDescription(
                key="last_update",
                name="Last Update",
                device_class=SensorDeviceClass.TIMESTAMP,
            ),
        )
    )

    async_add_entities(entities)
    return True


class LastUpdateSensor(SensorEntity):
    """State sensor."""

    _attr_icon = "mdi:clock-edit-outline"

    def __init__(
        self,
        coordinator: EvLoadBalancingCoordinator,
        entity_description: SensorEntityDescription,
    ) -> None:
        """Initialize the entity."""
        # super().__init__(planner)
        self._coordinator = coordinator
        self.entity_description = entity_description
        self._attr_device_info = coordinator.get_device_info()
        self._attr_name = self._coordinator.name + " " + entity_description.name
        self._attr_unique_id = (
            (DOMAIN + "_" + self._attr_name).lower().replace(".", "").replace(" ", "_")
        )

    @property
    def native_value(self):
        """Output state."""
        state = STATE_UNKNOWN
        if self._coordinator.last_update is not None:
            state = self._coordinator.last_update
        _LOGGER.debug(
            'Returning state "%s" of sensor "%s"',
            state,
            self.unique_id,
        )
        return state

    async def async_added_to_hass(self) -> None:
        """Load the last known state when added to hass."""
        await super().async_added_to_hass()
        self._coordinator.register_output_listener_entity(self.update_callback)

    def update_callback(self) -> None:
        """Call from planner that new data available."""
        self.schedule_update_ha_state()
