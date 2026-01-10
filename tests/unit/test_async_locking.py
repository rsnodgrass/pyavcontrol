"""
Test async locking behavior with mocked devices.

Tests verify that:
1. Single device operations are serialized (one at a time)
2. Multiple devices can operate concurrently
3. Send+receive are atomic for each device
4. No global lock serializes ALL devices
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, Mock

import pytest

from pyavcontrol.client.async_client import DeviceClientAsync
from pyavcontrol.library.model import DeviceModel


@pytest.fixture
def sample_device_definition() -> dict:
    """Sample device definition for testing."""
    return {
        'info': {'manufacturer': 'Test', 'models': ['Test']},
        'api': {},
    }


class TestAsyncLocking:
    """Test async locking with mocked connections."""

    @pytest.mark.asyncio
    async def test_single_device_serializes_operations(
        self, sample_device_definition: dict
    ) -> None:
        """Verify that operations on a single device are serialized."""
        call_order: list[tuple[str, bytes]] = []

        async def mock_send_delay(
            data: bytes, wait_for_response: bool = False
        ) -> bytes:
            call_order.append(('start', data))
            await asyncio.sleep(0.1)
            call_order.append(('end', data))
            return b'OK\r'

        mock_conn = AsyncMock()
        mock_conn.send = mock_send_delay
        mock_conn.is_async = Mock(return_value=True)

        model = DeviceModel('test_device', sample_device_definition)
        loop = asyncio.get_event_loop()
        client = DeviceClientAsync(model, mock_conn, loop)

        tasks = [
            client.send_raw(b'CMD1\r', wait_for_response=True),
            client.send_raw(b'CMD2\r', wait_for_response=True),
            client.send_raw(b'CMD3\r', wait_for_response=True),
        ]

        await asyncio.gather(*tasks)

        # verify operations were serialized
        assert call_order[0] == ('start', b'CMD1\r')
        assert call_order[1] == ('end', b'CMD1\r')
        assert call_order[2] == ('start', b'CMD2\r')
        assert call_order[3] == ('end', b'CMD2\r')
        assert call_order[4] == ('start', b'CMD3\r')
        assert call_order[5] == ('end', b'CMD3\r')

    @pytest.mark.asyncio
    async def test_multiple_devices_concurrent_operations(
        self, sample_device_definition: dict
    ) -> None:
        """Verify that multiple devices can operate concurrently."""
        active_devices: set[int] = set()
        max_concurrent = 0

        async def mock_send_track(
            device_id: int, data: bytes, wait_for_response: bool = False
        ) -> bytes:
            nonlocal max_concurrent
            active_devices.add(device_id)
            max_concurrent = max(max_concurrent, len(active_devices))
            await asyncio.sleep(0.1)
            active_devices.remove(device_id)
            return b'OK\r'

        loop = asyncio.get_event_loop()
        clients = []

        for i in range(3):
            mock_conn = AsyncMock()
            mock_conn.send = (
                lambda d, wait_for_response=False, dev_id=i: mock_send_track(
                    dev_id, d, wait_for_response
                )
            )
            mock_conn.is_async = Mock(return_value=True)

            model = DeviceModel(f'test_device_{i}', sample_device_definition)
            client = DeviceClientAsync(model, mock_conn, loop)
            clients.append(client)

        tasks = [
            clients[0].send_raw(b'CMD1\r', wait_for_response=True),
            clients[1].send_raw(b'CMD2\r', wait_for_response=True),
            clients[2].send_raw(b'CMD3\r', wait_for_response=True),
        ]

        await asyncio.gather(*tasks)

        assert max_concurrent == 3, f'Expected 3 concurrent, got {max_concurrent}'

    @pytest.mark.asyncio
    async def test_send_receive_atomic(self, sample_device_definition: dict) -> None:
        """Verify send+receive is atomic (not interruptible)."""
        operation_states: list[str] = []

        async def mock_send_with_receive(
            data: bytes, wait_for_response: bool = False
        ) -> bytes:
            operation_states.append(f'send:{data.decode()}')
            await asyncio.sleep(0.05)
            if wait_for_response:
                operation_states.append(f'receive:{data.decode()}')
            return b'OK\r'

        mock_conn = AsyncMock()
        mock_conn.send = mock_send_with_receive
        mock_conn.is_async = Mock(return_value=True)

        model = DeviceModel('test_device', sample_device_definition)
        loop = asyncio.get_event_loop()
        client = DeviceClientAsync(model, mock_conn, loop)

        tasks = [
            client.send_raw(b'CMD1\r', wait_for_response=True),
            client.send_raw(b'CMD2\r', wait_for_response=True),
        ]

        await asyncio.gather(*tasks)

        # verify send+receive are atomic (not interleaved)
        assert operation_states == [
            'send:CMD1\r',
            'receive:CMD1\r',
            'send:CMD2\r',
            'receive:CMD2\r',
        ]

    @pytest.mark.asyncio
    async def test_no_global_lock_exists(self, sample_device_definition: dict) -> None:
        """Verify there's no global lock blocking all devices."""
        start_times: dict[int, float] = {}
        end_times: dict[int, float] = {}

        async def mock_send_timed(
            device_id: int, data: bytes, wait_for_response: bool = False
        ) -> bytes:
            start_times[device_id] = asyncio.get_event_loop().time()
            await asyncio.sleep(0.2)
            end_times[device_id] = asyncio.get_event_loop().time()
            return b'OK\r'

        loop = asyncio.get_event_loop()
        clients = []

        for i in range(3):
            mock_conn = AsyncMock()
            mock_conn.send = (
                lambda d, wait_for_response=False, dev_id=i: mock_send_timed(
                    dev_id, d, wait_for_response
                )
            )
            mock_conn.is_async = Mock(return_value=True)

            model = DeviceModel(f'test_device_{i}', sample_device_definition)
            client = DeviceClientAsync(model, mock_conn, loop)
            clients.append(client)

        start = asyncio.get_event_loop().time()
        await asyncio.gather(
            clients[0].send_raw(b'CMD\r'),
            clients[1].send_raw(b'CMD\r'),
            clients[2].send_raw(b'CMD\r'),
        )
        total_time = asyncio.get_event_loop().time() - start

        # with concurrent: ~200ms, with global lock: ~600ms
        assert total_time < 0.4, f'Took {total_time:.2f}s, suggests global lock'
