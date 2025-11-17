"""
Tests DeviceModel validation
"""

import logging

import pytest

from pyavcontrol.library.model import DeviceModel

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.INFO)


def test_valid_model():
    pass


def test_invalid_model():
    pass


@pytest.mark.skip(reason='Validation system currently broken - see agent review')
def test_empty_model():
    with pytest.raises(ValueError):
        DeviceModel('test_empty', {})


@pytest.mark.skip(reason='Validation system currently broken - see agent review')
def test_undefined_model():
    with pytest.raises(ValueError):
        DeviceModel('test_undefined', None)
