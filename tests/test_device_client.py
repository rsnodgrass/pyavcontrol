"""
Tests several interfaces of the MX-160 to confirm that typical usage patterns of a
DeviceClient work.
"""

import asyncio
import unittest

import serial

from pyavcontrol import ZoneStatus, get_async_mcintosh, get_mcintosh
from tests import create_dummy_port


class TestDeviceClient(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        pass
    
    def setUp(self):
        self.library = None
        self.client = None
        self.responses = {}

        class DummyDevice:
            def send():
                pass
        
    def test_request_with_response(self):
        pass

    def test_request_without_response(self):
        pass

    def test_timeout(self):
        with self.assertRaises(asyncio.TimeoutError):
            self.client.power.turn_off()

    def test_missing_arguments(self):
        pass

    def test_response_dictionary_parsing(self):
        pass

if __name__ == "__main__":
    unittest.main()
