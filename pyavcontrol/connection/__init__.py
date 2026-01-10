"""Connection implementations for serial and IP communication."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from pyavcontrol.const import DEFAULT_ENCODING

if TYPE_CHECKING:
    from asyncio import AbstractEventLoop
    from collections.abc import Callable

LOG = logging.getLogger(__name__)


class DeviceConnection(ABC):
    """
    Abstract base class that defines communication APIs for device connections.

    Subclasses implement either synchronous or asynchronous communication
    with A/V equipment over RS232 or IP.
    """

    @abstractmethod
    def is_connected(self) -> bool:
        """
        Check if the connection is established.

        Returns:
            True if connected to the device.
        """

    @abstractmethod
    def send(
        self,
        data: bytes,
        callback: Callable[[bytes], None] | None = None,
        wait_for_response: bool = False,
    ) -> bytes | None:
        """
        Send data to the remote device.

        Args:
            data: Bytes to send
            callback: Optional callback for async response handling
            wait_for_response: Whether to wait for and return a response

        Returns:
            Response bytes if wait_for_response is True, otherwise None.
        """

    def is_async(self) -> bool:
        """
        Check if this connection is asynchronous.

        Returns:
            True if this is an async connection implementation.
        """
        return False

    def __repr__(self) -> str:
        return self.__class__.__name__


class NullConnection(DeviceConnection):
    """
    NullConnection sends all data to /dev/null.

    Useful for testing without real hardware.
    """

    def is_connected(self) -> bool:
        return True

    def send(
        self,
        data: bytes,
        callback: Callable[[bytes], None] | None = None,
        wait_for_response: bool = False,
    ) -> None:
        pass


class Connection:
    """Factory for creating device connections."""

    @staticmethod
    def create(
        url: str,
        connection_config: dict[str, Any] | None = None,
        event_loop: AbstractEventLoop | None = None,
    ) -> DeviceConnection:
        """
        Create a Connection instance for the given device.

        If an event_loop is provided, returns an async implementation.
        Otherwise returns a synchronous implementation.

        Args:
            url: pyserial-compatible URL (e.g. '/dev/ttyUSB0' or 'socket://host:7000/')
            connection_config: Optional pyserial configuration overrides
            event_loop: Optional event loop for async operation

        Returns:
            DeviceConnection instance.
        """
        if connection_config is None:
            connection_config = {}

        LOG.debug(f'Connecting to {url}: %s', connection_config)

        if event_loop:
            from pyavcontrol.connection.async_connection import AsyncDeviceConnection

            return AsyncDeviceConnection(url, connection_config, event_loop)

        from pyavcontrol.connection.sync_connection import SyncDeviceConnection

        return SyncDeviceConnection(url, connection_config)
