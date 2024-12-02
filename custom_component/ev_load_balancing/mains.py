"""Handling Mains currents input."""

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable, Coroutine
import logging

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class Mains(ABC):
    """Base class for Mains extractor."""

    # def __init__(self) -> None:
    #     """Initialize base class."""
    #     pass

    @abstractmethod
    def current_phase1(self) -> float | None:
        """Get phase 1 current."""


class MainsSlimmelezer(Mains):
    """Slimmelezer mains extractor."""

    def __init__(self) -> None:
        """Initilalize Slimmelezer extractor."""
        pass

    def current_phase1(self) -> float | None:
        """Get phase 1 current."""
        current = 1
        _LOGGER.debug("Returning current %f for phase 1", current)
        return current
