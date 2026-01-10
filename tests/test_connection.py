"""Tests for connection implementations."""

from __future__ import annotations

from unittest.mock import Mock, patch

from pyavcontrol.connection import Connection, NullConnection


class TestNullConnection:
    """Test NullConnection implementation."""

    def test_is_connected_always_true(self) -> None:
        """NullConnection is always connected."""
        conn = NullConnection()
        assert conn.is_connected() is True

    def test_send_returns_none(self) -> None:
        """NullConnection send returns None."""
        conn = NullConnection()
        result = conn.send(b'test data')
        assert result is None

    def test_send_with_callback(self) -> None:
        """NullConnection ignores callback."""
        conn = NullConnection()
        callback_called = False

        def callback(data: bytes) -> None:
            nonlocal callback_called
            callback_called = True

        conn.send(b'test', callback=callback)
        assert not callback_called

    def test_is_async_returns_false(self) -> None:
        """NullConnection is synchronous."""
        conn = NullConnection()
        assert conn.is_async() is False


class TestConnectionFactory:
    """Test Connection factory method."""

    def test_create_sync_connection(self) -> None:
        """Test creating synchronous connection."""
        with patch(
            'pyavcontrol.connection.sync_connection.serial.serial_for_url'
        ) as mock_serial:
            mock_port = Mock()
            mock_serial.return_value = mock_port

            conn = Connection.create('/dev/ttyUSB0', {'baudrate': 9600})

            assert conn is not None
            assert not conn.is_async()

    def test_create_async_connection(self) -> None:
        """Test creating asynchronous connection with event loop."""
        import asyncio

        loop = asyncio.new_event_loop()
        try:
            with patch('pyavcontrol.connection.async_connection.asyncio.create_task'):
                conn = Connection.create(
                    '/dev/ttyUSB0', {'baudrate': 9600}, event_loop=loop
                )

                assert conn is not None
                assert conn.is_async()
        finally:
            loop.close()

    def test_create_with_empty_config(self) -> None:
        """Test creating connection with no config."""
        with patch(
            'pyavcontrol.connection.sync_connection.serial.serial_for_url'
        ) as mock_serial:
            mock_port = Mock()
            mock_serial.return_value = mock_port

            conn = Connection.create('/dev/ttyUSB0')

            assert conn is not None


class TestDeviceConnectionInterface:
    """Test DeviceConnection abstract interface."""

    def test_repr_returns_class_name(self) -> None:
        """Test default repr implementation."""
        conn = NullConnection()
        assert 'NullConnection' in repr(conn)
