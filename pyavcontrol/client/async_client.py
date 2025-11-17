import asyncio
import logging
from collections.abc import Callable

from ..connection import DeviceConnection
from ..library.model import DeviceModel
from .base import DeviceClient

LOG = logging.getLogger(__name__)


class DeviceClientAsync(DeviceClient):
    """Asynchronous client for communicating with devices via the provided connection"""

    def __init__(self, model: DeviceModel, connection: DeviceConnection, loop):
        super().__init__(model, connection)
        self._loop = loop
        self._callback = None
        self._lock = asyncio.Lock()  # instance-level lock for this specific device

        if not connection.is_async():
            raise RuntimeError('Provided DeviceConnection is not asynchronous!')

    @property
    def is_async(self):
        """:return: true since this client is asynchronous"""
        return True

    async def send_raw(self, data: bytes, wait_for_response=False):
        """Send raw data to the device with instance-level locking."""
        async with self._lock:
            # if LOG.isEnabledFor(logging.DEBUG):
            #    LOG.debug(f'Sending {self._connection!r}: {data}')
            return await self._connection.send(
                data, wait_for_response=wait_for_response
            )

    async def register_callback(self, callback: Callable[[str], None]) -> None:
        """Register a callback for received messages."""
        async with self._lock:
            if not callable(callback):
                raise ValueError('Callback is not Callable')
            self._callback = callback

    async def received_message(self):
        """Handle received message by calling the registered callback."""
        async with self._lock:
            self._loop.call_soon(self._callback)
