"""Handling Chargers."""

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable, Coroutine
import logging

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class Charger(ABC):
    """Base class for Charger robot."""

    # def __init__(self) -> None:
    #     """Initialize base class."""
    #     pass

    @abstractmethod
    def set_limits(self, phase1: float, phase2: float, phase3: float) -> bool:
        """Set charger limits."""


class ChargerEasee(Charger):
    """Slimmelezer mains extractor."""

    def __init__(self) -> None:
        """Initilalize Slimmelezer extractor."""
        pass

    def set_limits(self, phase1: float, phase2: float, phase3: float) -> bool:
        """Set charger limits."""
        _LOGGER.debug(
            "Setting limits: phase 1 %f, phase 2 %f, phase 3 %f", phase1, phase2, phase3
        )
        return True
