"""Config flow for EvLoadBalancing integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import device_registry as dr, selector

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class EvLoadBalancingConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """EvLoadBalancing config flow."""

    VERSION = 0
    MINOR_VERSION = 1
    data = None
    options = None
    _reauth_entry: config_entries.ConfigEntry | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle initial user step."""
        errors: dict[str, str] = {}

        mains_type = "slimmelezer"
        charger_type = "easee"

        if user_input is not None:
            self.data = user_input
            self.data["mains_type"] = mains_type
            self.data["charger_type"] = charger_type

            self.options = {}
            await self.async_set_unique_id(
                self.data[CONF_NAME] + "_" + mains_type + "_" + charger_type
            )
            self._abort_if_unique_id_configured()

            _LOGGER.debug(
                'Creating entry "%s" with data "%s" and oprions %s',
                self.unique_id,
                self.data,
                self.options,
            )
            return self.async_create_entry(
                title=self.data[CONF_NAME], data=self.data, options=self.options
            )

        mains = await self._async_get_devices(mains_type)
        chargers = await self._async_get_devices(charger_type)

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME): str,
                vol.Required("mains_device_id"): vol.In(mains),
                vol.Required("mains_limit", default=20): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=6,
                        max=80,
                        step=1,
                        unit_of_measurement="ampere",
                    )
                ),
                vol.Required("charger_device_id"): vol.In(chargers),
                vol.Required("charger_expires", default=10): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=1,
                        max=30,
                        step=1,
                        unit_of_measurement="minutes",
                    )
                ),
            }
        )

        placeholders = {
            #     CONF_TYPE: CONF_TYPE_LIST,
            #     CONF_NP_ENTITY: selected_entities,
        }

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            description_placeholders=placeholders,
            errors=errors,
        )

    async def _async_get_devices(self, search_str: str):
        devices = {}
        for device_entry in dr.async_get(self.hass).devices.values():
            if (
                device_entry.manufacturer
                and search_str.lower() in device_entry.manufacturer.strip().lower()
            ) or (
                device_entry.name
                and search_str.lower() in device_entry.name.strip().lower()
            ):
                devices[device_entry.id] = device_entry.name
        return devices
