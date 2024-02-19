"""
Tests DeviceClient interface using  the MX-160 to confirm that typical usage patterns work.
"""

import pytest
import logging
import asyncio

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.INFO)


def test_request_with_response():
    pass


def test_request_without_response():
    pass


def test_timeout():
    #with pytest.raises(asyncio.TimeoutError):
    #    client.power.turn_off()
    pass

def test_missing_arguments():
    pass


def test_response_dictionary_parsing():
    pass
