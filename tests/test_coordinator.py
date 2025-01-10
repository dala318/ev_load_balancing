"""planner tests."""

from unittest import mock

from custom_components.ev_load_balancing import EvLoadBalancingCoordinator

# from pytest_homeassistant_custom_component.async_mock import patch
# from pytest_homeassistant_custom_component.common import (
#     MockModule,
#     MockPlatform,
#     mock_integration,
#     mock_platform,
# )
from custom_components.ev_load_balancing.const import DOMAIN
import pytest

from homeassistant import config_entries
from homeassistant.const import ATTR_NAME, ATTR_UNIT_OF_MEASUREMENT

# from homeassistant.components import sensor
# from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

NAME = "My balancer"

CONF_ENTRY = config_entries.ConfigEntry(
    data={
        ATTR_NAME: NAME,
        "mains_type": "template",
        "charger_type": "template",
        "developer_mode": False,
    },
    options={
        "mains": {
            "mains_phase1": "phase_1_template",
            "mains_phase2": "phase_2_template",
            "mains_phase3": "phase_3_template",
            "mains_limit": 20,
        },
        "charger": {
            "charger_phase1": "phase_1_template",
            "charger_phase2": "phase_2_template",
            "charger_phase3": "phase_3_template",
            "charger_active": "active_template",
            "charger_limit": "limit_template",
            "charger_command": "command_template",
            "phase_auto_matching": False,
        },
        "phases": {
            "mains_phase1": "PHASE1",
            "mains_phase2": "PHASE2",
            "mains_phase3": "PHASE3",
            "charger_phase1": "PHASE1",
            "charger_phase2": "PHASE2",
            "charger_phase3": "PHASE3",
        },
    },
    domain=DOMAIN,
    version=0,
    minor_version=3,
    source="user",
    title=NAME,
    unique_id="123456",
    discovery_keys=None,
)


@pytest.mark.asyncio
async def test_coordinator_init(hass):
    """Test the coordinator initialization."""

    coordinator = EvLoadBalancingCoordinator(hass, CONF_ENTRY)

    assert coordinator.name == NAME
