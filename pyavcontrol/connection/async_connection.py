"""Asynchronous serial connection implementation."""

from __future__ import annotations

import asyncio
import functools
import logging
import time
from functools import wraps
from typing import TYPE_CHECKING, Any

from ratelimit import limits
from serial_asyncio import create_serial_connection

from pyavcontrol.config import CONFIG
from pyavcontrol.connection import DeviceConnection
from pyavcontrol.const import DEFAULT_ENCODING, DEFAULT_TIMEOUT

if TYPE_CHECKING:
    from asyncio import AbstractEventLoop
    from collections.abc import Awaitable, Callable

LOG = logging.getLogger(__name__)

ONE_MINUTE = 60


class AsyncDeviceConnection(DeviceConnection):
    """
    Asynchronous device connection using pyserial-asyncio.

    Provides non-blocking serial communication with automatic
    reconnection and rate limiting.
    """

    __slots__ = (
        '_url',
        '_connection_config',
        '_legacy_connection',
        '_event_loop',
        '_encoding',
    )

    def __init__(
        self,
        url: str,
        connection_config: dict[str, Any],
        loop: AbstractEventLoop,
    ) -> None:
        """
        Initialize asynchronous serial connection.

        Args:
            url: pyserial-compatible URL for the connection
            connection_config: Serial configuration parameters
            loop: Event loop for async operations
        """
        self._url = url
        self._connection_config = connection_config
        self._legacy_connection: RS232ControlProtocol | None = None
        self._event_loop = loop
        self._encoding = connection_config.get(CONFIG.encoding, DEFAULT_ENCODING)

        # schedule connection after returning (construction is synchronous)
        asyncio.create_task(self._connect())

    def __repr__(self) -> str:
        return f'{self.__class__.__name__} / {self._url}'

    async def _connect(self) -> None:
        """Establish connection to the device."""
        if self._legacy_connection is not None:
            return

        try:
            self._legacy_connection = await _async_get_rs232_connection(
                self._url,
                self._connection_config,
                self._connection_config,
                self._event_loop,
            )
        except Exception:
            LOG.exception(f'Failed connecting: url={self._url}')

    def is_async(self) -> bool:
        """Return True since this is an async connection."""
        return True

    async def is_connected(self) -> bool:
        """Check if connection is established."""
        return self._legacy_connection is not None

    @staticmethod
    def ensure_connected(
        method: Callable[..., Awaitable[Any]],
    ) -> Callable[..., Awaitable[Any]]:
        """
        Decorator to ensure connection before method execution.

        Automatically attempts reconnection if not connected.
        """
        @wraps(method)
        async def wrapper(
            self: AsyncDeviceConnection, *args: Any, **kwargs: Any
        ) -> Any:
            try:
                await self._connect()
                return await method(self, *args, **kwargs)
            except Exception:
                LOG.warning(f'Cannot connect to {self._url}!')
                raise

        return wrapper

    @ensure_connected
    async def send(
        self,
        data: bytes,
        callback: Callable[[bytes], None] | None = None,
        wait_for_response: bool = False,
    ) -> bytes | None:
        """
        Send data to the device asynchronously.

        Args:
            data: Bytes to send
            callback: Optional callback for response handling
            wait_for_response: Whether to wait for and return response

        Returns:
            Response bytes if wait_for_response is True, otherwise None.
        """
        if not self._legacy_connection:
            LOG.error('Missing connection!')
            return None

        return await self._legacy_connection.send(
            data, wait_for_response=wait_for_response
        )


class RS232ControlProtocol(asyncio.Protocol):
    """
    Asyncio protocol implementation for RS232 serial communication.

    Handles connection lifecycle, data buffering, and response handling.
    """

    __slots__ = (
        '_url',
        '_config',
        '_connection_config',
        '_loop',
        '_encoding',
        '_min_time_between_commands',
        '_last_send',
        '_timeout',
        '_transport',
        '_connected',
        '_queue',
        '_lock',
    )

    def __init__(
        self,
        serial_port: str,
        config: dict[str, Any],
        connection_config: dict[str, Any],
        loop: AbstractEventLoop,
    ) -> None:
        """
        Initialize protocol handler.

        Args:
            serial_port: Serial port URL
            config: Protocol configuration
            connection_config: Connection parameters
            loop: Event loop
        """
        super().__init__()
        self._url = serial_port
        self._config = config
        self._connection_config = connection_config
        self._loop = loop
        self._encoding = connection_config.get(CONFIG.encoding, DEFAULT_ENCODING)
        self._min_time_between_commands = config.get(
            CONFIG.min_time_between_commands, 0
        )
        self._last_send = time.time() - 1
        self._timeout = connection_config.get(CONFIG.timeout, DEFAULT_TIMEOUT)
        self._transport: Any = None
        self._connected = asyncio.Event()
        self._queue: asyncio.Queue[bytes] = asyncio.Queue()
        self._lock = asyncio.Lock()

    def connection_made(self, transport: Any) -> None:
        """Handle successful connection."""
        self._transport = transport
        LOG.debug(f'Port {self._url} opened {self._transport}')
        self._connected.set()

    def data_received(self, data: bytes) -> None:
        """Handle incoming data by queueing it."""
        asyncio.ensure_future(self._queue.put(data))

    def connection_lost(self, exc: Exception | None) -> None:
        """Handle connection loss."""
        LOG.debug(f'Port {self._url} closed')

    async def _reset_buffers(self) -> None:
        """Reset all input and output buffers."""
        self._transport.serial.reset_output_buffer()
        self._transport.serial.reset_input_buffer()
        while not self._queue.empty():
            self._queue.get_nowait()

    async def send(
        self,
        data: bytes,
        callback: Callable[[bytes], None] | None = None,
        wait_for_response: bool = False,
    ) -> bytes | None:
        """
        Send data with locking and rate limiting.

        Args:
            data: Bytes to send
            callback: Optional callback for response
            wait_for_response: Whether to wait for response

        Returns:
            Response bytes if wait_for_response is True.
        """
        async with self._lock:
            try:
                await asyncio.wait_for(self._connected.wait(), self._timeout)
            except TimeoutError:
                LOG.debug(f'Timeout sending data to {self._url}, no connection!')
                raise

            @limits(calls=1, period=self._min_time_between_commands)
            async def write_rate_limited(data_bytes: bytes) -> None:
                LOG.debug(f'>> {self._url}: %s', data_bytes)
                self._transport.serial.write(data_bytes)

            await self._reset_buffers()
            await write_rate_limited(data)

            if callback or wait_for_response:
                result = await self._receive_response(data)
                LOG.debug(f'<< {self._url}: %s', result)
                if callback:
                    await callback(result)
                return result

            return None

    async def _receive_response(self, request: bytes) -> bytes:
        """
        Wait for and return response data.

        Args:
            request: Original request (for logging)

        Returns:
            Response bytes.

        Raises:
            TimeoutError: If response times out
        """
        data = bytearray()
        try:
            data += await asyncio.wait_for(self._queue.get(), self._timeout)
            return bytes(data)

        except TimeoutError:
            @limits(calls=2, period=ONE_MINUTE)
            def log_timeout() -> None:
                LOG.info(
                    f"Timeout @ {self._timeout}s for {self._url} request '%s'; "
                    f"received '%s'",
                    request,
                    data,
                )

            log_timeout()
            raise


async def _async_get_rs232_connection(
    serial_port: str,
    config: dict[str, Any],
    connection_config: dict[str, Any],
    loop: AbstractEventLoop,
) -> RS232ControlProtocol:
    """
    Create and return an RS232 protocol connection.

    Args:
        serial_port: Serial port URL
        config: Protocol configuration
        connection_config: Connection parameters
        loop: Event loop

    Returns:
        Connected RS232ControlProtocol instance.
    """
    factory = functools.partial(
        RS232ControlProtocol, serial_port, config, connection_config, loop
    )

    LOG.info(f'Connecting to {serial_port}: {connection_config}')
    _, protocol = await create_serial_connection(
        loop, factory, serial_port, **connection_config
    )
    return protocol
