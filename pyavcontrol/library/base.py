"""Base classes for device model libraries."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
import re

from pyavcontrol.library.model import DeviceModel


@dataclass(frozen=True, slots=True)
class DeviceModelSummary:
    """Summary information about a device model."""

    manufacturer: str
    model_name: str
    model_id: str


def filter_models_by_regex(
    models: set[DeviceModelSummary], regex: str
) -> set[DeviceModelSummary]:
    """
    Filter device models by matching manufacturer, model name, or ID.

    Args:
        models: Set of DeviceModelSummary to filter
        regex: Regular expression pattern to match

    Returns:
        Set of matching DeviceModelSummary objects.
    """
    pattern = re.compile(regex)
    matches: set[DeviceModelSummary] = set()

    for summary in models:
        if (
            pattern.match(summary.manufacturer)
            or pattern.match(summary.model_name)
            or pattern.match(summary.model_id)
        ):
            matches.add(summary)

    return matches


class DeviceModelLibraryBase(ABC):
    """Abstract base class for device model libraries."""

    @abstractmethod
    def load_model(self, name: str) -> DeviceModel | None:
        """
        Load a device model by ID or file path.

        Args:
            name: Model ID or complete path to a definition file

        Returns:
            DeviceModel instance or None if not found.
        """

    @abstractmethod
    def supported_model_ids(self) -> frozenset[str]:
        """
        Get all model IDs supported by this library.

        Returns:
            Frozen set of model identifier strings.
        """

    @abstractmethod
    def supported_models(self) -> frozenset[DeviceModelSummary]:
        """
        Get summaries of all supported models.

        Returns:
            Frozen set of DeviceModelSummary objects.
        """
