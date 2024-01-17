import logging
import asyncio
import functools
import time
from abc import ABC
from functools import wraps

from ratelimit import limits
from serial_asyncio import create_serial_connection

from pyavcontrol.connection import DeviceConnection

from ..config import CONFIG
from ..const import *  # noqa: F403

LOG = logging.getLogger(__name__)

ONE_MINUTE = 60

# FIXME: for a specific instance we do not want communication to happen
# simultaneously...for now just lock ALL accesses to ANY device.
async_lock = asyncio.Lock()


def locked_coro(coro):
    @wraps(coro)
    async def wrapper(*args, **kwargs):
        async with async_lock:
            return await coro(*args, **kwargs)

    return wrapper


class AsyncDeviceConnection(DeviceConnection, ABC):
    def __init__(self, url: str, connection_config: dict, loop):
        """
        :param url: pyserial compatible url
        :param connection_config: pyserial connection config (plus additional attributes timeout/encoding)
        """
        super().__init__()

        self._url = url
        self._connection_config = connection_config
        self._event_loop = loop

        # FIXME: I think encoding should be moved up a level
        self._encoding = connection_config.get(CONFIG.encoding, DEFAULT_ENCODING)

        # schedule connecting after returning (since construction of this class is executed
        # in a synchronous context)
        asyncio.create_task(self._connect())

    def __repr__(self) -> str:
        return f'{self.__name__} / {self._url}'

    async def _connect(self) -> None:
        # FIXME: hacky...merge this old code into this class eventually...
        self._legacy_connection = await async_get_rs232_connection(
            self._url,
            self._connection_config,  # self._config,
            self._connection_config,
            self._connection_config.get(CONFIG.format, {}),  # self._protocol_def,
            self._event_loop,
        )

    async def is_connected(self) -> bool:
        return self._legacy_connection

    async def send(self, data: bytes, callback=None):
        reply = False  # depends on action! FIXME
        return await self._legacy_connection.send(self, data, wait_for_reply=reply)


async def async_get_rs232_connection(
    serial_port: str, config: dict, connection_config: dict, protocol_def: dict, loop
):
    # ensure only a single, ordered command is sent to RS232 at a time (non-reentrant lock)
    def locked_method(method):
        @wraps(method)
        async def wrapper(self, *method_args, **method_kwargs):
            async with self._lock:
                return await method(self, *method_args, **method_kwargs)

        return wrapper

    # check if connected, and abort calling provided method if no connection before timeout
    def ensure_connected(method):
        @wraps(method)
        async def wrapper(self, *method_args, **method_kwargs):
            try:
                await asyncio.wait_for(self._connected.wait(), self._timeout)
            except Exception:
                LOG.debug(f'Timeout sending data to {self._url}, no connection!')
                return
            return await method(self, *method_args, **method_kwargs)

        return wrapper

    class RS232ControlProtocol(asyncio.Protocol):
        def __init__(
            self, serial_port, config, connection_config, protocol_config, loop
        ):
            super().__init__()

            self._url = serial_port
            self._config = config
            self._connection_config = connection_config
            self._loop = loop

            # FIXME: this should actually be on the client layer and not connection itself
            self._encoding = self._connection_config.get(
                CONFIG.encoding, DEFAULT_ENCODING
            )

            self._min_time_between_commands = self._config.get(
                CONFIG.min_time_between_commands, 0
            )

            self._last_send = time.time() - 1
            self._timeout = self._connection_config.get(CONFIG.timeout, DEFAULT_TIMEOUT)

            self._transport = None
            self._connected = asyncio.Event()
            self._q = asyncio.Queue()

            # ensure only a single, ordered command is sent to RS232 at a time (non-reentrant lock)
            self._lock = asyncio.Lock()

        def connection_made(self, transport):
            self._transport = transport
            LOG.debug(f'Port {self._url} opened {self._transport}')
            self._connected.set()

        def data_received(self, data):
            #            LOG.debug(f"Received {self._url}: %s", data)
            asyncio.ensure_future(self._q.put(data))  # , loop=self._loop)

        def connection_lost(self, exc):
            LOG.debug(f'Port {self._url} closed')

        async def _reset_buffers(self):
            """Reset all input and output buffers"""
            self._transport.serial.reset_output_buffer()
            self._transport.serial.reset_input_buffer()
            while not self._q.empty():
                self._q.get_nowait()

        @locked_method
        @ensure_connected
        async def send(self, data: bytes, callback=None, wait_for_reply=False):
            @limits(calls=1, period=self._min_time_between_commands)
            async def write_rate_limited(data: bytes):
                LOG.debug(f'>> {self._url}: %s', data)
                self._transport.serial.write(data)

            # clear all buffers of any data waiting to be read before sending the request
            await self._reset_buffers()

            await write_rate_limited(data)

            # FIXME: move away from this with callbacks instead
            if callback or wait_for_reply:
                result = await self.receive_response(data)
                LOG.debug(f'<< {self._url}: %s', result)
                if callback:
                    await callback(result)
                return result

        async def receive_response(self, request):
            data = bytearray()
            try:
                data += await asyncio.wait_for(self._q.get(), self._timeout)
                return data

            except asyncio.TimeoutError:
                # log up to two times within a time period to avoid saturating the logs
                @limits(calls=2, period=ONE_MINUTE)
                def log_timeout():
                    LOG.info(
                        f"Timeout @ {self._timeout}s for {self._url} request '%s'; received '%s'",
                        request,
                        data,
                    )

                log_timeout()
                raise

    factory = functools.partial(
        RS232ControlProtocol, serial_port, config, connection_config, protocol_def, loop
    )

    LOG.info(f'Connecting to {serial_port}: {connection_config}')
    _, protocol = await create_serial_connection(
        loop, factory, serial_port, **connection_config
    )
    return protocol
