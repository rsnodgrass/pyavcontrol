import logging
from collections.abc import Callable

from ..connection import DeviceConnection
from ..connection.async_connection import locked_coro
from ..library.model import DeviceModel
from .base import DeviceClient

LOG = logging.getLogger(__name__)

class DeviceClientAsync(DeviceClient):
    """Asynchronous client for communicating with devices via the provided connection"""

    def __init__(self, model: DeviceModel, connection: DeviceConnection, loop):
        super().__init__(model, connection)
        self._loop = loop
        self._callback = None

        if not connection.is_async():
            raise RuntimeError(f"Provided DeviceConnection is not asynchronous!")

    @property
    def is_async(self):
        """:return: always true since this client implementation is asynchronous"""
        return True

    @locked_coro
    async def send_raw(self, data: bytes, wait_for_response=False):
        #if LOG.isEnabledFor(logging.DEBUG):
        #    LOG.debug(f'Sending {self._connection!r}: {data}')
        return await self._connection.send(data, wait_for_response=wait_for_response)

    @locked_coro
    def register_callback(self, callback: Callable[[str], None]) -> None:
        if not callable(callback):
            raise ValueError('Callback is not Callable')
        self._callback = callback

    @locked_coro
    async def received_message(self):
        await self._loop.call_soon(self._callback)
