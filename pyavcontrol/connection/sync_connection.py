import logging
from abc import ABC
from functools import wraps
from threading import RLock

import serial
from ratelimit import limits

from pyavcontrol.connection import DeviceConnection

from ..config import CONFIG
from ..const import DEFAULT_ENCODING, DEFAULT_EOL

LOG = logging.getLogger(__name__)

sync_lock = RLock()


def synchronized(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        with sync_lock:
            return func(*args, **kwargs)

    return wrapper


class SyncDeviceConnection(DeviceConnection, ABC):
    """
    Synchronous device connection implementation (NOT YET IMPLEMENTED)
    """

    def __init__(self, url: str, connection_config: dict):
        """
        :param url: pyserial compatible url
        """
        self._url = url
        self._connection_config = connection_config

        self._encoding = connection_config.get(CONFIG.encoding, DEFAULT_ENCODING)

        # FIXME: remove the following
        config = connection_config # FIXME: remove
        self._eol = config.get(CONFIG.message_eol, DEFAULT_EOL).encode(self._encoding)

        # FIXME: all min time between commands should probably be at the client level and
        # not at the raw connection... move up!
        self._min_time_between_commands = config.get(
            CONFIG.min_time_between_commands, 0
        )

        # FIXME: contemplate on this more, do we really want to reset/clear
        self._clear_before_new_commands = connection_config.get(
            CONFIG.clear_before_new_commands, True
        )

        self._port = serial.serial_for_url(self._url, **self._connection_config)

    def __repr__(self) -> str:
#        return f'{self.__class__.__name__}->{self._url}'
        return f'{self._url}'

    def encoding(self) -> str:
        return self._encoding

    def _reset_buffers(self):
        self._port.reset_output_buffer()
        self._port.reset_input_buffer()

    def send(self, data: bytes, callback=None, wait_for_response: bool=False):
        """
        :param data: data bytes sent to the device
        :param callback: (optional)
        :param wait_for_response: (optional)
        :return: string returned by device
        """

        @limits(calls=1, period=self._min_time_between_commands)
        def write_rate_limited(data_bytes: bytes):
            LOG.debug(f'>> {self._url}: %s', data_bytes)
            # send data and force flush to send immediately
            self._port.write(data_bytes)
            self._port.flush()

        # clear any pending transactions if a response is expected
        if response_expected := (callback or wait_for_response):
            if self._clear_before_new_commands:
                self._reset_buffers()

        write_rate_limited(data)

        # if the caller has requested to receive the result, send it to any
        # provided callback and return the result
        if response_expected:
            LOG.debug(f"Waiting for response (EOL={self._eol})...")

            result = self.handle_receive()
            LOG.debug(f'<< {self._url}: %s', result)

            if callback:
                callback(result)
            return result

    def handle_receive(self) -> bytes:
        skip = 0

        len_eol = len(self._eol)

        # FIXME: implement a much better receive mechanism, without timeouts.

        # receive
        result = bytearray()
        while True:
            c = self._port.read(1)
            if not c:
                ret = bytes(result)
                LOG.info(ret)
                raise serial.SerialTimeoutException(
                    'Connection timed out! Last received bytes {}'.format(
                        [hex(a) for a in result]
                    )
                )
            result += c
            if len(result) > skip and result[-len_eol:] == self._eol:
                break

        ret = bytes(result)
        LOG.debug(f'Received {self._url} "%s"', ret)
        return ret
