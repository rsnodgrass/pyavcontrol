"""Tests for DeviceClient interface."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest

from pyavcontrol.client.async_client import DeviceClientAsync
from pyavcontrol.client.base import DeviceClient
from pyavcontrol.client.sync_client import DeviceClientSync
from pyavcontrol.connection import NullConnection
from pyavcontrol.library.model import DeviceModel


class TestDeviceClientCreation:
    """Test DeviceClient factory method."""

    def test_create_sync_client(
        self, sample_device_definition: dict[str, Any]
    ) -> None:
        """Test creating a synchronous client."""
        model = DeviceModel('test_device', sample_device_definition)
        connection = NullConnection()

        client = DeviceClient.create(model, connection)

        assert client is not None
        assert not client.is_async
        assert client.model.id == 'test_device'

    def test_create_async_client(
        self, sample_device_definition: dict[str, Any]
    ) -> None:
        """Test creating an asynchronous client."""
        import asyncio

        model = DeviceModel('test_device', sample_device_definition)
        mock_connection = AsyncMock()
        mock_connection.is_async = Mock(return_value=True)
        loop = asyncio.new_event_loop()

        try:
            client = DeviceClient.create(model, mock_connection, event_loop=loop)

            assert client is not None
            assert client.is_async
        finally:
            loop.close()

    def test_client_has_action_groups(
        self, sample_device_definition: dict[str, Any]
    ) -> None:
        """Test that client has injected action groups."""
        model = DeviceModel('test_device', sample_device_definition)
        connection = NullConnection()

        client = DeviceClient.create(model, connection)

        # should have power and volume groups from the definition
        assert hasattr(type(client), 'power')
        assert hasattr(type(client), 'volume')

    def test_action_group_has_methods(
        self, sample_device_definition: dict[str, Any]
    ) -> None:
        """Test that action groups have the expected methods."""
        model = DeviceModel('test_device', sample_device_definition)
        connection = NullConnection()

        client = DeviceClient.create(model, connection)

        # power group should have on and off methods
        power_group = getattr(type(client), 'power')
        assert hasattr(power_group, 'on')
        assert hasattr(power_group, 'off')


class TestDeviceClientSync:
    """Test synchronous client functionality."""

    def test_send_raw(self, sample_device_definition: dict[str, Any]) -> None:
        """Test sending raw data through sync client."""
        model = DeviceModel('test_device', sample_device_definition)
        mock_conn = Mock()
        mock_conn.send = Mock(return_value=b'OK\r')

        client = DeviceClientSync(model, mock_conn)
        result = client.send_raw(b'TEST\r', wait_for_response=True)

        assert result == b'OK\r'
        mock_conn.send.assert_called_once()

    def test_register_callback(
        self, sample_device_definition: dict[str, Any]
    ) -> None:
        """Test registering a callback."""
        model = DeviceModel('test_device', sample_device_definition)
        mock_conn = Mock()
        client = DeviceClientSync(model, mock_conn)

        def my_callback(msg: str) -> None:
            pass

        client.register_callback(my_callback)
        assert client._callback == my_callback

    def test_register_invalid_callback_raises(
        self, sample_device_definition: dict[str, Any]
    ) -> None:
        """Test that non-callable raises ValueError."""
        model = DeviceModel('test_device', sample_device_definition)
        mock_conn = Mock()
        client = DeviceClientSync(model, mock_conn)

        with pytest.raises(ValueError, match='Callback is not Callable'):
            client.register_callback('not a callable')  # type: ignore


class TestDeviceClientAsync:
    """Test asynchronous client functionality."""

    @pytest.mark.asyncio
    async def test_send_raw(
        self, sample_device_definition: dict[str, Any]
    ) -> None:
        """Test sending raw data through async client."""
        import asyncio

        model = DeviceModel('test_device', sample_device_definition)
        mock_conn = AsyncMock()
        mock_conn.is_async = Mock(return_value=True)
        mock_conn.send = AsyncMock(return_value=b'OK\r')
        loop = asyncio.get_event_loop()

        client = DeviceClientAsync(model, mock_conn, loop)
        result = await client.send_raw(b'TEST\r', wait_for_response=True)

        assert result == b'OK\r'
        mock_conn.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_client_requires_async_connection(
        self, sample_device_definition: dict[str, Any]
    ) -> None:
        """Test that async client requires async connection."""
        import asyncio

        model = DeviceModel('test_device', sample_device_definition)
        mock_conn = Mock()
        mock_conn.is_async = Mock(return_value=False)
        loop = asyncio.get_event_loop()

        with pytest.raises(RuntimeError, match='not asynchronous'):
            DeviceClientAsync(model, mock_conn, loop)

    @pytest.mark.asyncio
    async def test_register_callback(
        self, sample_device_definition: dict[str, Any]
    ) -> None:
        """Test registering a callback on async client."""
        import asyncio

        model = DeviceModel('test_device', sample_device_definition)
        mock_conn = AsyncMock()
        mock_conn.is_async = Mock(return_value=True)
        loop = asyncio.get_event_loop()

        client = DeviceClientAsync(model, mock_conn, loop)

        def my_callback(msg: str) -> None:
            pass

        await client.register_callback(my_callback)
        assert client._callback == my_callback


class TestClientEncoding:
    """Test encoding handling."""

    def test_default_encoding(
        self, sample_device_definition: dict[str, Any]
    ) -> None:
        """Test default ASCII encoding."""
        model = DeviceModel('test_device', sample_device_definition)
        connection = NullConnection()

        client = DeviceClient.create(model, connection)

        assert client.encoding() == 'ascii'

    def test_custom_encoding(self) -> None:
        """Test custom encoding from model."""
        definition = {
            'info': {'manufacturer': 'Test', 'models': ['Model']},
            'format': {'encoding': 'utf-8'},
            'api': {},
        }
        model = DeviceModel('test', definition)
        connection = NullConnection()

        client = DeviceClient.create(model, connection)

        assert client.encoding() == 'utf-8'
