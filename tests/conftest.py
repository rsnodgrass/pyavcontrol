"""
Pytest configuration and fixtures for testing pyavcontrol.

All tests use mocked serial/IP connections to avoid needing real hardware.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest


@pytest.fixture
def mock_serial_transport() -> Mock:
    """Mock pyserial transport for RS232 connections."""
    transport = Mock()
    transport.serial = Mock()
    transport.serial.write = Mock()
    transport.serial.reset_output_buffer = Mock()
    transport.serial.reset_input_buffer = Mock()
    return transport


@pytest.fixture
def mock_serial_protocol(mock_serial_transport: Mock) -> AsyncMock:
    """Mock RS232 protocol for testing device communication."""
    protocol = AsyncMock()
    protocol._transport = mock_serial_transport
    protocol._connected = asyncio.Event()
    protocol._connected.set()
    protocol._q = asyncio.Queue()
    protocol.send = AsyncMock(return_value=b'OK\r')
    protocol.receive_response = AsyncMock(return_value=b'OK\r')
    return protocol


@pytest.fixture
def mock_connection(mock_serial_protocol: AsyncMock) -> AsyncMock:
    """Mock AsyncDeviceConnection for testing clients."""
    connection = AsyncMock()
    connection._legacy_connection = mock_serial_protocol
    connection.send = AsyncMock(return_value=b'OK\r')
    connection.is_async = Mock(return_value=True)
    connection.is_connected = AsyncMock(return_value=True)
    return connection


@pytest.fixture
def sample_device_definition() -> dict[str, Any]:
    """Sample device definition for testing."""
    return {
        'id': 'test_device',
        'info': {
            'manufacturer': 'Test Corp',
            'models': ['Test Model 100'],
            'type': 'processor',
            'tested': True,
        },
        'connection': {
            'rs232': {
                'baudrate': 9600,
                'bytesize': 8,
                'parity': 'N',
                'stopbits': 1,
                'timeout': 1.0,
            }
        },
        'protocol': {
            'encoding': 'ascii',
            'command_eol': '\r',
            'message_eol': '\r',
        },
        'vars': {
            'power': {'type': 'int', 'min': 0, 'max': 1},
            'volume': {'type': 'int', 'min': 0, 'max': 100},
        },
        'api': {
            'power': {
                'actions': {
                    'on': {
                        'description': 'Turn power on',
                        'cmd': {'fstring': 'PWR1\r'},
                        'msg': {'regex': 'PWR1'},
                    },
                    'off': {
                        'description': 'Turn power off',
                        'cmd': {'fstring': 'PWR0\r'},
                        'msg': {'regex': 'PWR0'},
                    },
                }
            },
            'volume': {
                'actions': {
                    'set': {
                        'description': 'Set volume',
                        'cmd': {'fstring': 'VOL{volume}\r'},
                        'msg': {
                            'regex': r'VOL(?P<volume>\d+)',
                            'tests': {'VOL50': {'volume': 50}},
                        },
                    },
                    'get': {
                        'description': 'Get current volume',
                        'cmd': {'fstring': 'VOL?\r'},
                        'msg': {
                            'regex': r'VOL(?P<volume>\d+)',
                            'tests': {'VOL25': {'volume': 25}},
                        },
                    },
                }
            },
        },
    }


@pytest.fixture
def yaml_library_path() -> Path:
    """Path to YAML device definitions."""
    return Path(__file__).parent.parent / 'pyavcontrol' / 'data' / 'src'


@pytest.fixture
def all_device_yaml_files(yaml_library_path: Path) -> list[Path]:
    """List all device YAML files for integration testing."""
    return list(yaml_library_path.glob('*.yaml'))
