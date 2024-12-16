"""Config flow for EvLoadBalancing integration."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import ConfigEntryError
from homeassistant.helpers import device_registry as dr, selector

from .const import (
    CONF_CHARGER_DEVICE_ID,
    CONF_CHARGER_EXPIRES,
    CONF_CHARGER_PHASE1,
    CONF_CHARGER_PHASE2,
    CONF_CHARGER_PHASE3,
    CONF_CHARGER_TYPE,
    CONF_DEVELOPER_MODE,
    CONF_DEVICES,
    CONF_MAINS_DEVICE_ID,
    CONF_MAINS_LIMIT,
    CONF_MAINS_PHASE1,
    CONF_MAINS_PHASE2,
    CONF_MAINS_PHASE3,
    CONF_MAINS_TYPE,
    CONF_PHASE_AUTO_MATCHING,
    CONF_PHASES,
    DOMAIN,
    NAME_EASEE,
    NAME_SLIMMELEZER,
)
from .coordinator import Phases, get_charger, get_mains

_LOGGER = logging.getLogger(__name__)


class PhaseLearningFailed(ConfigEntryError):
    """Special error if phase learning fails."""


class EvLoadBalancingConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """EvLoadBalancing config flow."""

    VERSION = 0
    MINOR_VERSION = 2
    data = {}
    options = {}

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
            self.data = user_input
            return await self.async_step_devices()

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME): str,
                vol.Required(CONF_MAINS_TYPE): vol.In(mains_types),
                vol.Required(CONF_CHARGER_TYPE): vol.In(charger_types),
                vol.Required(CONF_DEVELOPER_MODE, default=False): bool,
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
        """Handle device selection step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self.options[CONF_DEVICES] = user_input

            await self.async_set_unique_id(
                self.options[CONF_DEVICES][CONF_MAINS_DEVICE_ID]
                + "_"
                + self.options[CONF_DEVICES][CONF_CHARGER_DEVICE_ID]
            )
            self._abort_if_unique_id_configured()

            if self.options[CONF_DEVICES][CONF_PHASE_AUTO_MATCHING]:
                return self.async_step_auto_phases()

            return await self.async_step_phases()

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
                vol.Required(CONF_PHASE_AUTO_MATCHING, default=False): bool,
            }
        )

        return self.async_show_form(
            step_id="devices",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_auto_phases(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle auto-phase matching."""
        # errors: dict[str, str] = {}

        mains = get_mains(
            self.hass,
            None,
            self.data,
            self.options,
        )
        mains.update()

        charger = get_charger(
            self.hass,
            None,
            self.data,
            self.options,
        )

        phase_matches: dict[Phases, Phases] = {
            Phases.PHASE1: None,
            Phases.PHASE2: None,
            Phases.PHASE3: None,
        }
        for c_phase in Phases:
            # Deactivate all phases on charger
            await charger.async_set_limits(0.0, 0.0, 0.0)
            asyncio.sleep(10)
            base_values = {
                Phases.PHASE1: mains.get_phase(Phases.PHASE1).actual_current,
                Phases.PHASE2: mains.get_phase(Phases.PHASE2).actual_current,
                Phases.PHASE3: mains.get_phase(Phases.PHASE3).actual_current,
            }

            # Activate one phase
            await charger.async_set_limits(
                (10.0 if c_phase == Phases.PHASE1 else 0.0),
                (10.0 if c_phase == Phases.PHASE2 else 0.0),
                (10.0 if c_phase == Phases.PHASE3 else 0.0),
            )
            asyncio.sleep(10)

            #  Try to find one phase that has increased significantly in load
            for attempt in range(120):
                found = False
                for m_phase in Phases:
                    if (
                        base_values[m_phase] + 6
                        < mains.get_phase(m_phase).actual_current
                    ):
                        phase_matches[c_phase] = m_phase
                        _LOGGER.debug(
                            "Found match for charger %s in mains %s after %u attempts",
                            c_phase.name,
                            m_phase.name,
                            attempt,
                        )
                        found = True

                # Break if found or wait a second and try again
                if found:
                    break
                asyncio.sleep(1)

            else:
                raise PhaseLearningFailed(
                    f"Could not find a matching mains phase for charger phase {c_phase.name}"
                )

        if (
            any(m is None for m in phase_matches.values())  # A phase was not detected
            or len(set(phase_matches.values())) < 3  # Unique phases was not detected
        ):
            _LOGGER.warning("Failed to match phases, will continue to manual setup")
        else:
            _LOGGER.info("Matching found, will continue to manual step to confirm")
            self.options[CONF_PHASES] = {
                CONF_MAINS_PHASE1: phase_matches[Phases.PHASE1].name,
                CONF_MAINS_PHASE2: phase_matches[Phases.PHASE2].name,
                CONF_MAINS_PHASE3: phase_matches[Phases.PHASE3].name,
                CONF_CHARGER_PHASE1: Phases.PHASE1.name,
                CONF_CHARGER_PHASE2: Phases.PHASE2.name,
                CONF_CHARGER_PHASE3: Phases.PHASE3.name,
            }

        return await self.async_step_phases()

    async def async_step_phases(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle phase matching step."""
        errors: dict[str, str] = {}

        if CONF_PHASES not in self.options:
            self.options[CONF_PHASES] = {
                CONF_MAINS_PHASE1: Phases.PHASE1.name,
                CONF_MAINS_PHASE2: Phases.PHASE2.name,
                CONF_MAINS_PHASE3: Phases.PHASE3.name,
                CONF_CHARGER_PHASE1: Phases.PHASE1.name,
                CONF_CHARGER_PHASE2: Phases.PHASE2.name,
                CONF_CHARGER_PHASE3: Phases.PHASE3.name,
            }

        if user_input is not None:
            self.options[CONF_PHASES] = user_input

            if (
                user_input[CONF_MAINS_PHASE1] == user_input[CONF_MAINS_PHASE2]
                or user_input[CONF_MAINS_PHASE2] == user_input[CONF_MAINS_PHASE3]
                or user_input[CONF_MAINS_PHASE3] == user_input[CONF_MAINS_PHASE1]
                or user_input[CONF_CHARGER_PHASE1] == user_input[CONF_CHARGER_PHASE2]
                or user_input[CONF_CHARGER_PHASE2] == user_input[CONF_CHARGER_PHASE3]
                or user_input[CONF_CHARGER_PHASE3] == user_input[CONF_CHARGER_PHASE1]
            ):
                errors["base"] = "duplicate_phase_matching"

            else:
                _LOGGER.debug(
                    'Creating entry "%s" with data "%s" and options %s',
                    self.unique_id,
                    self.data,
                    self.options,
                )
                return self.async_create_entry(
                    title=self.data[CONF_NAME], data=self.data, options=self.options
                )

        mains = get_mains(
            self.hass,
            None,
            self.data,
            self.options,
        )
        mains_phases = [
            selector.SelectOptionDict(value=p.name, label=mains.get_phase(p).name)
            for p in Phases
        ]

        charger = get_charger(
            self.hass,
            None,
            self.data,
            self.options,
        )
        charger_phases = [
            selector.SelectOptionDict(value=p.name, label=charger.get_phase(p).name)
            for p in Phases
        ]

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_MAINS_PHASE1,
                    default=self.options[CONF_PHASES][CONF_MAINS_PHASE1],
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=mains_phases,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    ),
                ),
                vol.Required(
                    CONF_CHARGER_PHASE1,
                    default=self.options[CONF_PHASES][CONF_CHARGER_PHASE1],
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=charger_phases,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    ),
                ),
                vol.Required(
                    CONF_MAINS_PHASE2,
                    default=self.options[CONF_PHASES][CONF_MAINS_PHASE2],
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=mains_phases,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    ),
                ),
                vol.Required(
                    CONF_CHARGER_PHASE2,
                    default=self.options[CONF_PHASES][CONF_CHARGER_PHASE2],
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=charger_phases,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    ),
                ),
                vol.Required(
                    CONF_MAINS_PHASE3,
                    default=self.options[CONF_PHASES][CONF_MAINS_PHASE3],
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=mains_phases,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    ),
                ),
                vol.Required(
                    CONF_CHARGER_PHASE3,
                    default=self.options[CONF_PHASES][CONF_CHARGER_PHASE3],
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=charger_phases,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    ),
                ),
            }
        )

        return self.async_show_form(
            step_id="phases",
            data_schema=schema,
            errors=errors,
        )

    @staticmethod
    @config_entries.callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> EvLoadBalancingOptionsFlow:
        """Create the options flow."""
        return EvLoadBalancingOptionsFlow(config_entry)


class EvLoadBalancingOptionsFlow(config_entries.OptionsFlowWithConfigEntry):
    """EvLoadBalancing options flow."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Manually update & reload the config entry after options change.
            errors["base"] = "not_implemented"

            # changed = self.hass.config_entries.async_update_entry(
            #     self.config_entry,
            #     options=user_input,
            # )
            # if changed:
            #     await self.hass.config_entries.async_reload(self.config_entry.entry_id)
            # return self.async_create_entry(title="", data=user_input)

        schema = vol.Schema(
            {
                vol.Required("show_things"): bool,
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema, errors=errors)
        # return self.async_show_form(
        #     step_id="init",
        #     data_schema=self.add_suggested_values_to_schema(
        #         schema, self.config_entry.options
        #     ),
        # )
