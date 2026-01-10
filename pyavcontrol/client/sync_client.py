"""Synchronous device client implementation."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from pyavcontrol.client.base import DeviceClient
from pyavcontrol.connection.sync_connection import synchronized

if TYPE_CHECKING:
    from collections.abc import Callable

    from pyavcontrol.connection import DeviceConnection
    from pyavcontrol.library.model import DeviceModel

LOG = logging.getLogger(__name__)


class DeviceClientSync(DeviceClient):
    """
    Synchronous client for communicating with A/V devices.

    Uses thread-safe synchronization for concurrent access.
    """

    __slots__ = ('_callback',)

    def __init__(self, model: DeviceModel, connection: DeviceConnection) -> None:
        """
        Initialize sync client.

        Args:
            model: Device model definition
            connection: Synchronous connection to the device
        """
        super().__init__(model, connection)
        self._callback: Callable[[str], None] | None = None

    @synchronized
    def send_raw(
        self,
        data: bytes,
        wait_for_response: bool = False,
        return_raw: bool = False,
    ) -> bytes | None:
        """
        Send raw data to the device with thread-safe locking.

        Args:
            data: Bytes to send
            wait_for_response: Whether to wait for response
            return_raw: Whether to return raw bytes

        Returns:
            Response bytes if wait_for_response is True.
        """
        return self._connection.send(data, wait_for_response=wait_for_response)

    @synchronized
    def register_callback(self, callback: Callable[[str], None]) -> None:
        """
        Register a callback for received messages.

        Args:
            callback: Callable to invoke on message receipt

        Raises:
            ValueError: If callback is not callable
        """
        if not callable(callback):
            raise ValueError('Callback is not Callable')
        self._callback = callback

    @synchronized
    def received_message(self) -> None:
        """Handle received message by calling the registered callback."""
        if self._callback:
            LOG.error(f'Callback not implemented: {self._callback}')
