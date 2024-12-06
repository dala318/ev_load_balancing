"""config_flow tests."""

from unittest import mock

from custom_components.nordpool_planner import config_flow
from custom_components.nordpool_planner.const import *
import pytest

# from pytest_homeassistant_custom_component.async_mock import patch
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import ATTR_NAME, ATTR_UNIT_OF_MEASUREMENT
from homeassistant.helpers import selector

PRICES_ENTITY_NAME = "sensor.nordpool_ent"

SCHEMA_COPY = vol.Schema(
    {
        vol.Required(ATTR_NAME): str,
        vol.Required(CONF_TYPE): selector.SelectSelector(
            selector.SelectSelectorConfig(options=CONF_TYPE_LIST),
        ),
        vol.Required(CONF_PRICES_ENTITY): selector.SelectSelector(
            selector.SelectSelectorConfig(options=[PRICES_ENTITY_NAME]),
        ),
        vol.Required(CONF_ACCEPT_COST_ENTITY, default=False): bool,
        vol.Required(CONF_ACCEPT_RATE_ENTITY, default=False): bool,
        vol.Required(CONF_HIGH_COST_ENTITY, default=False): bool,
    }
)


# @pytest.mark.asyncio
# async def test_flow_init(hass):
#     """Test the initial flow."""
#     result = await hass.config_entries.flow.async_init(
#         config_flow.DOMAIN, context={"source": "user"}
#     )

#     expected = {
#         "data_schema": SCHEMA_COPY,
#         # "data_schema": config_flow.DATA_SCHEMA,
#         "description_placeholders": None,
#         "errors": {},
#         "flow_id": mock.ANY,
#         "handler": "nordpool_planner",
#         "step_id": "user",
#         "type": "form",
#     }
#     assert expected == result
