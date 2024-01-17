"""
Test behavior of the connection implementions
"""

import asyncio
import unittest

import serial

from pyavcontrol import ZoneStatus, get_async_mcintosh, get_mcintosh
from tests import create_dummy_port


class TestAsyncConnection(unittest.TestCase):
    def setUp(self):
        class DummyDevice:
            def send():
                pass
        
    def test_timeout(self):
        pass

if __name__ == "__main__":
    unittest.main()
