"""Synchronous serial connection implementation."""

from __future__ import annotations

import logging
from functools import wraps
from threading import RLock
from typing import TYPE_CHECKING, Any

import serial
from ratelimit import limits

from pyavcontrol.config import CONFIG
from pyavcontrol.connection import DeviceConnection
from pyavcontrol.const import DEFAULT_ENCODING, DEFAULT_EOL

if TYPE_CHECKING:
    from collections.abc import Callable

LOG = logging.getLogger(__name__)

# module-level reentrant lock for thread-safe operations
_sync_lock = RLock()


def synchronized(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator to synchronize method calls using a module-level lock.

    Ensures thread-safe access to serial port operations.
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        with _sync_lock:
            return func(*args, **kwargs)
    return wrapper


class SyncDeviceConnection(DeviceConnection):
    """
    Synchronous device connection implementation using pyserial.

    Provides thread-safe serial communication with rate limiting
    and configurable timeouts.
    """

    __slots__ = (
        '_url',
        '_connection_config',
        '_encoding',
        '_eol',
        '_min_time_between_commands',
        '_clear_before_new_commands',
        '_port',
    )

    def __init__(self, url: str, connection_config: dict[str, Any]) -> None:
        """
        Initialize synchronous serial connection.

        Args:
            url: pyserial-compatible URL for the connection
            connection_config: Serial configuration parameters
        """
        self._url = url
        self._connection_config = connection_config
        self._encoding = connection_config.get(CONFIG.encoding, DEFAULT_ENCODING)
        self._eol = connection_config.get(CONFIG.message_eol, DEFAULT_EOL).encode(
            self._encoding
        )
        self._min_time_between_commands = connection_config.get(
            CONFIG.min_time_between_commands, 0
        )
        self._clear_before_new_commands = connection_config.get(
            CONFIG.clear_before_new_commands, True
        )
        self._port = serial.serial_for_url(self._url, **self._connection_config)

    def __repr__(self) -> str:
        return self._url

    def is_connected(self) -> bool:
        """Check if the serial port is open."""
        return self._port.is_open

    def encoding(self) -> str:
        """Return the character encoding used for this connection."""
        return self._encoding

    def _reset_buffers(self) -> None:
        """Clear both input and output serial buffers."""
        self._port.reset_output_buffer()
        self._port.reset_input_buffer()

    def send(
        self,
        data: bytes,
        callback: Callable[[bytes], None] | None = None,
        wait_for_response: bool = False,
    ) -> bytes | None:
        """
        Send data to the device with optional response handling.

        Args:
            data: Bytes to send
            callback: Optional callback for response handling
            wait_for_response: Whether to wait for and return response

        Returns:
            Response bytes if wait_for_response is True, otherwise None.

        Raises:
            serial.SerialTimeoutException: If response times out
        """
        @limits(calls=1, period=self._min_time_between_commands)
        def write_rate_limited(data_bytes: bytes) -> None:
            LOG.debug(f'>> {self._url}: %s', data_bytes)
            self._port.write(data_bytes)
            self._port.flush()

        # clear pending data if response expected
        response_expected = callback or wait_for_response
        if response_expected and self._clear_before_new_commands:
            self._reset_buffers()

        write_rate_limited(data)

        if response_expected:
            LOG.debug(f'Waiting for response (EOL={self._eol})...')
            result = self._receive()
            LOG.debug(f'<< {self._url}: %s', result)

            if callback:
                callback(result)
            return result

        return None

    def _receive(self) -> bytes:
        """
        Receive data until end-of-line marker is found.

        Returns:
            Complete response bytes.

        Raises:
            serial.SerialTimeoutException: If no data received within timeout
        """
        result = bytearray()
        len_eol = len(self._eol)

        while True:
            char = self._port.read(1)
            if not char:
                LOG.info('Received so far: %s', bytes(result))
                raise serial.SerialTimeoutException(
                    f'Connection timed out! Last received bytes {[hex(b) for b in result]}'
                )
            result += char
            if len(result) >= len_eol and result[-len_eol:] == self._eol:
                break

        response = bytes(result)
        LOG.debug(f'Received {self._url} "%s"', response)
        return response
