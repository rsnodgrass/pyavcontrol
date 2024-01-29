import logging
from collections.abc import Callable

from ..connection import DeviceConnection
from ..connection.sync_connection import synchronized
from ..library.model import DeviceModel
from .base import DeviceClient

LOG = logging.getLogger(__name__)


class DeviceClientSync(DeviceClient):
    """Synchronous client for communicating with devices via the provided connection"""

    def __init__(self, model: DeviceModel, connection: DeviceConnection):
        super().__init__(model, connection)
        self._callback = None

    @synchronized
    def send_raw(self, data: bytes, wait_for_response: bool=False):
        #if LOG.isEnabledFor(logging.DEBUG):
        #    LOG.debug(f'Sending {self._connection!r}: {data}')
        return self._connection.send(data, wait_for_response=wait_for_response)


    @synchronized
    def register_callback(self, callback: Callable[[str], None]) -> None:
        if not callable(callback):
            raise ValueError('Callback is not Callable')
        self._callback = callback

    @synchronized
    def received_message(self):
        if self._callback:
            LOG.error(f'Callback not implemented!! {self._callback}')  # FIXME
            # self._loop.call_soon(cb)
