"""
Tests DeviceModel validation
"""

import pytest
import logging

from pyavcontrol.library.model import DeviceModel

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.INFO)


def test_valid_model():
    pass

def test_invalid_model():
    pass

def test_empty_model():
    with pytest.raises(ValueError):
        DeviceModel('test_empty', {})

def test_undefined_model():
    with pytest.raises(ValueError):
        DeviceModel('test_undefined', None)
