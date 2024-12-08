"""Config flow for EvLoadBalancing integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import device_registry as dr, selector

from .const import (
    CONF_CHARGER_DEVICE_ID,
    CONF_CHARGER_EXPIRES,
    CONF_CHARGER_TYPE,
    CONF_MAINS_DEVICE_ID,
    CONF_MAINS_LIMIT,
    CONF_MAINS_TYPE,
    DOMAIN,
    NAME_EASEE,
    NAME_SLIMMELEZER,
)

_LOGGER = logging.getLogger(__name__)


# @staticmethod
# @config_entries.callback
# def async_get_options_flow(
#     config_entry: config_entries.ConfigEntry,
# ) -> EvLoadBalancingOptionsFlow:
#     """Create the options flow."""
#     return EvLoadBalancingOptionsFlow()


# class EvLoadBalancingOptionsFlow(config_entries.OptionsFlow):
#     """EvLoadBalancing options flow."""

#     async def async_step_init(
#         self, user_input: dict[str, Any] | None = None
#     ) -> FlowResult:
#         """Manage the options."""
#         if user_input is not None:
#             return self.async_create_entry(data=user_input)

#         schema = vol.Schema(
#             {
#                 vol.Required("show_things"): bool,
#             }
#         )

#         return self.async_show_form(
#             step_id="init",
#             data_schema=self.add_suggested_values_to_schema(
#                 schema, self.config_entry.options
#             ),
#         )


class EvLoadBalancingConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """EvLoadBalancing config flow."""

    VERSION = 0
    MINOR_VERSION = 1
    data = {}
    options = {}
    # _reauth_entry: config_entries.ConfigEntry | None = None

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

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle initial user step."""
        errors: dict[str, str] = {}

        mains_types = [NAME_SLIMMELEZER]
        charger_types = [NAME_EASEE]

        if user_input is not None:
            self.data[CONF_NAME] = user_input[CONF_NAME]
            self.data[CONF_MAINS_TYPE] = user_input[CONF_MAINS_TYPE]
            self.data[CONF_CHARGER_TYPE] = user_input[CONF_CHARGER_TYPE]

            return await self.async_step_devices()

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME): str,
                vol.Required(CONF_MAINS_TYPE): vol.In(mains_types),
                vol.Required(CONF_CHARGER_TYPE): vol.In(charger_types),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_devices(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle initial user step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self.options = user_input

            await self.async_set_unique_id(
                self.options[CONF_MAINS_DEVICE_ID]
                + "_"
                + self.options[CONF_CHARGER_DEVICE_ID]
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

        mains = await self._async_get_devices(self.data[CONF_MAINS_TYPE])
        chargers = await self._async_get_devices(self.data[CONF_CHARGER_TYPE])

        schema = vol.Schema(
            {
                vol.Required(CONF_MAINS_DEVICE_ID): vol.In(mains),
                vol.Required(CONF_MAINS_LIMIT, default=20): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=6,
                        max=80,
                        step=1,
                        unit_of_measurement="ampere",
                    )
                ),
                vol.Required(CONF_CHARGER_DEVICE_ID): vol.In(chargers),
                vol.Required(CONF_CHARGER_EXPIRES, default=10): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=1,
                        max=30,
                        step=1,
                        unit_of_measurement="minutes",
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="devices",
            data_schema=schema,
            errors=errors,
        )
