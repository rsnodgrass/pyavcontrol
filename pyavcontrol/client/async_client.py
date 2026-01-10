"""Asynchronous device client implementation."""

from __future__ import annotations

import logging
import asyncio
from typing import TYPE_CHECKING

from pyavcontrol.client.base import DeviceClient

if TYPE_CHECKING:
    from asyncio import AbstractEventLoop
    from collections.abc import Callable

    from pyavcontrol.connection import DeviceConnection
    from pyavcontrol.library.model import DeviceModel

LOG = logging.getLogger(__name__)


class DeviceClientAsync(DeviceClient):
    """
    Asynchronous client for communicating with A/V devices.

    Uses instance-level locking to ensure commands are serialized
    per-device while allowing concurrent operations across devices.
    """

    __slots__ = ('_callback', '_lock', '_loop')

    def __init__(
        self,
        model: DeviceModel,
        connection: DeviceConnection,
        loop: AbstractEventLoop,
    ) -> None:
        """
        Initialize async client.

        Args:
            model: Device model definition
            connection: Async connection to the device
            loop: Event loop for async operations

        Raises:
            RuntimeError: If connection is not asynchronous
        """
        super().__init__(model, connection)
        self._loop = loop
        self._callback: Callable[[str], None] | None = None
        self._lock = asyncio.Lock()

        if not connection.is_async():
            raise RuntimeError('Provided DeviceConnection is not asynchronous!')

    @property
    def is_async(self) -> bool:
        """Return True since this client is asynchronous."""
        return True

    async def send_raw(
        self,
        data: bytes,
        wait_for_response: bool = False,
        return_raw: bool = False,
    ) -> bytes | None:
        """
        Send raw data to the device with instance-level locking.

        Args:
            data: Bytes to send
            wait_for_response: Whether to wait for response
            return_raw: Whether to return raw bytes

        Returns:
            Response bytes if wait_for_response is True.
        """
        async with self._lock:
            return await self._connection.send(
                data, wait_for_response=wait_for_response
            )

    async def register_callback(self, callback: Callable[[str], None]) -> None:
        """
        Register a callback for received messages.

        Args:
            callback: Callable to invoke on message receipt

        Raises:
            ValueError: If callback is not callable
        """
        async with self._lock:
            if not callable(callback):
                raise ValueError('Callback is not Callable')
            self._callback = callback

    async def received_message(self) -> None:
        """Handle received message by calling the registered callback."""
        async with self._lock:
            if self._callback:
                self._loop.call_soon(self._callback)
