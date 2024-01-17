"""
Tests and example of a dynamically created Activity classes
"""

import asyncio
import unittest

import serial

from pyavcontrol import ZoneStatus, get_async_mcintosh, get_mcintosh
from tests import create_dummy_port


class TestMcIntoshMx160(unittest.TestCase):
    def setUp(self):
        self.library = None
        self.client = None
        self.responses = {}

        class DummyDevice:
            def send():
                pass
        

    def test_set_mute(self):
        #self.client.mute.on()
        #self.client.mute.off()
        #self.assertEqual(0, len(self.responses))
        pass

class TestAsyncXantech8(TestXantech8):
    def setUp(self):
        self.responses = {}

    def test_timeout(self):
        with self.assertRaises(asyncio.TimeoutError):
            self.mcintosh.set_source(3, 3)


if __name__ == "__main__":
    unittest.main()
