"""Handles the coordination between mains and charger."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry, Debouncer
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .chargers import Charger, ChargerPhase, ChargingState
from .chargers.easee import ChargerEasee
from .const import Phases
from .mains import Mains, MainsPhase
from .mains.slimmelezer import MainsSlimmelezer

_LOGGER = logging.getLogger(__name__)


class PhasePair:
    """Data analyzer per one phase."""

    def __init__(
        self,
        mains: MainsPhase,
        mains_limit: int,
        charger: ChargerPhase,
        charger_limit: int,
    ) -> None:
        """Pair of Charger and Mains phases."""
        self._mains = mains
        self._mains_limit = mains_limit
        self._charger = charger
        self._charger_limit = charger_limit

    def get_new_limit(self) -> float | None:
        """Calculate and return the propsed new limit for phase."""
        main_actual = self._mains.actual_current()
        charger_limit = self._charger.current_limit()
        if main_actual is None or charger_limit is None:
            return None
        spare = self._mains_limit - main_actual
        charger_new_limit = min(
            charger_limit + spare, self._charger_limit, self._mains_limit
        )
        _LOGGER.debug(
            "Calculated new circuit limit %f (actual: %f, old limit: %f)",
            charger_new_limit,
            main_actual,
            charger_limit,
        )
        return charger_new_limit


class EvLoadBalancingCoordinator(DataUpdateCoordinator):
    """Coordinator base class."""

    _mains: Mains
    _charger: Charger
    _pairs = []

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize my coordinator."""
        self._hass = hass
        super().__init__(
            hass,
            _LOGGER,
            name=config_entry.data.get(CONF_NAME),
            setup_method=self._async_setup_method,
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
            hass, self.async_request_refresh, "6b332da8a66c649c42f284a079a8bcaa", 20
        )

        # Charger
        self._charger = ChargerEasee(
            hass, self.async_request_refresh, "308b36c34ff3cd9766f693be289a8f3b"
        )

    def cleanup(self) -> None:
        """Cleanup any pending event listers etc."""
        self._mains.cleanup()
        self._charger.cleanup()

    async def async_shutdown(self) -> None:
        """Cancel any scheduled call, and ignore new runs."""
        self.cleanup()
        # self._shutdown_requested = True
        # self._async_unsub_refresh()
        # self._async_unsub_shutdown()
        # self._debounced_refresh.async_shutdown()

    def get_device_info(self) -> DeviceInfo:
        """Get device info to group entities."""
        return DeviceInfo(
            name=self.name,
            # manufacturer="LoadBalancing",
            entry_type=DeviceEntryType.SERVICE,
        )

    async def _async_setup_method(self) -> bool:
        """Setups call method."""
        mapping = {
            Phases.PHASE1: Phases.PHASE2,
            Phases.PHASE2: Phases.PHASE3,
            Phases.PHASE3: Phases.PHASE1,
        }

        for ch, ma in mapping.items():
            mains_phase = self._mains.get_phase(ma)
            mains_limit = self._mains.get_rated_limit()
            charger_phase = self._charger.get_phase(ch)
            charger_limit = self._charger.get_rated_limit()
            if (
                mains_phase is None
                or mains_limit is None
                or charger_phase is None
                or charger_limit is None
            ):
                self._pairs = []
                _LOGGER.warning(
                    "Got None value from dependency, aborting setup for now"
                )
                raise UpdateFailed("Got None value from dependency")
            self._pairs.append(
                PhasePair(
                    mains_phase,
                    mains_limit,
                    charger_phase,
                    charger_limit,
                )
            )
        self._shutdown_requested = False
        _LOGGER.info("Setup successful")
        # await self._async_update_method()
        return True

    async def _async_update_method(self):
        """Update call function."""
        _LOGGER.info("Updating service")

        if self._charger.charging_state not in [
            ChargingState.CHARGING,
            ChargingState.PENDING,
        ]:
            _LOGGER.debug("Skipping update since no charging active or pending")
            # return
            _LOGGER.warning(
                "Abort call due to charging not active disabled during development"
            )

        for pair in self._pairs:
            new_limit = pair.get_new_limit()
            if new_limit is None:
                _LOGGER.warning("Skipping update since None value found")
                return
            # _LOGGER.debug("Calculated new circuit limit %f", new_limit)
