"""Device model library for loading A/V equipment definitions."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyavcontrol.const import DEFAULT_MODEL_LIBRARIES

if TYPE_CHECKING:
    from asyncio import AbstractEventLoop

    from pyavcontrol.library.yaml_library import (
        YAMLDeviceModelLibraryAsync,
        YAMLDeviceModelLibrarySync,
    )


class DeviceModelLibrary:
    """Factory for creating device model library instances."""

    @staticmethod
    def create(
        library_dirs: tuple[str, ...] = DEFAULT_MODEL_LIBRARIES,
        event_loop: AbstractEventLoop | None = None,
    ) -> YAMLDeviceModelLibrarySync | YAMLDeviceModelLibraryAsync:
        """
        Create a DeviceModelLibrary for resolving device models.

        If an event_loop is provided, returns an async implementation.
        Otherwise returns a synchronous implementation.

        Args:
            library_dirs: Paths to search for model definitions
            event_loop: Optional event loop for async operation

        Returns:
            Library instance for loading device models.
        """
        if event_loop:
            from pyavcontrol.library.yaml_library import YAMLDeviceModelLibraryAsync

            return YAMLDeviceModelLibraryAsync(list(library_dirs), event_loop)

        from pyavcontrol.library.yaml_library import YAMLDeviceModelLibrarySync

        return YAMLDeviceModelLibrarySync(list(library_dirs))
