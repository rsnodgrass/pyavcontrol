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

    def __init__(self, url: str, config: dict, connection_config: dict):
        """
        :param url: pyserial compatible url
        """
        super.__init__()

        self._url = url
        self._config = config
        self._connection_config = connection_config

        self._encoding = connection_config.get(CONFIG.encoding, DEFAULT_ENCODING)
        self._eol = config.get(CONFIG.response_eol, DEFAULT_EOL).encode(self._encoding)

        # FIXME: all min time between commands should probably be at the client level and
        # not at the raw connection... move up!
        self._min_time_between_commands = self._config.get(
            CONFIG.min_time_between_commands, 0
        )

        # FIXME: contemplate on this more, do we really want to reset/clear
        self._clear_before_new_commands = connection_config.get(
            'clear_before_new_commands', False
        )

        self._port = serial.serial_for_url(self._url, **self._connection_config)

    def __repr__(self) -> str:
        return f'{self.__name__} / {self._url}'

    def encoding(self) -> str:
        return self._encoding

    def _reset_buffers(self):
        if self._clear_before_new_commands:
            self._port.reset_output_buffer()
            self._port.reset_input_buffer()

    def send(self, data: bytes, callback=None, wait_for_response=False):
        """
        :param data: request that is sent to the device
        :param skip: number of bytes to skip for end of transmission decoding
        :return:  string returned by device
        """

        @limits(calls=1, period=self._min_time_between_commands)
        def write_rate_limited(data: bytes):
            LOG.debug(f'>> {self._url}: %s', data)
            # send data and force flush to send immediately
            self._port.write(data)
            self._port.flush()

        # clear any pending transactions
        self._reset_buffers()

        write_rate_limited(data)

        # if the caller has requested to receive the result, send it to any
        # provided callback and return the result
        if callback or wait_for_response:
            result = self.handle_receive()
            LOG.debug(f'<< {self._url}: %s', result)
            if callback:
                callback(result)
            return result

    def handle_receive(self) -> str:
        skip = 0

        len_eol = len(self._eol)

        # FIXME: implement a much better receive mechanism, without timeouts.

        # receive
        result = bytearray()
        while True:
            c = self._port.read(1)
            # print(c)
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
        return ret.decode(self._encoding)
