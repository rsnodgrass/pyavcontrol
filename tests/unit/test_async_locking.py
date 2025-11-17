"""
Test async locking behavior with mocked devices.

Tests verify that:
1. Single device operations are serialized (one at a time)
2. Multiple devices can operate concurrently
3. Send+receive are atomic for each device
4. No global lock serializes ALL devices
"""

import asyncio
from unittest.mock import AsyncMock, Mock

import pytest

from pyavcontrol.client.async_client import DeviceClientAsync
from pyavcontrol.library.model import DeviceModel


@pytest.mark.asyncio
class TestAsyncLocking:
    """Test async locking with mocked connections"""

    async def test_single_device_serializes_operations(
        self, sample_device_definition, event_loop
    ):
        """Verify that operations on a single device are serialized"""

        # Track call order
        call_order = []

        async def mock_send_delay(data, wait_for_response=False):
            """Mock send that takes time to complete"""
            call_order.append(('start', data))
            await asyncio.sleep(0.1)  # Simulate I/O
            call_order.append(('end', data))
            return b'OK\r'

        # Create mock connection
        mock_conn = AsyncMock()
        mock_conn.send = mock_send_delay
        mock_conn.is_async = Mock(return_value=True)

        # Create client with mocked connection
        model = DeviceModel('test_device', sample_device_definition)
        client = DeviceClientAsync(model, mock_conn, event_loop)

        # Send multiple commands concurrently
        tasks = [
            client.send_raw(b'CMD1\r', wait_for_response=True),
            client.send_raw(b'CMD2\r', wait_for_response=True),
            client.send_raw(b'CMD3\r', wait_for_response=True),
        ]

        await asyncio.gather(*tasks)

        # Verify operations were serialized (each completes before next starts)
        assert call_order[0] == ('start', b'CMD1\r')
        assert call_order[1] == ('end', b'CMD1\r')
        assert call_order[2] == ('start', b'CMD2\r')
        assert call_order[3] == ('end', b'CMD2\r')
        assert call_order[4] == ('start', b'CMD3\r')
        assert call_order[5] == ('end', b'CMD3\r')

    async def test_multiple_devices_concurrent_operations(
        self, sample_device_definition, event_loop
    ):
        """Verify that multiple devices can operate concurrently"""

        # Track which device is active
        active_devices = set()
        max_concurrent = 0

        async def mock_send_track(device_id, data, wait_for_response=False):
            """Mock send that tracks concurrent operations"""
            nonlocal max_concurrent
            active_devices.add(device_id)
            max_concurrent = max(max_concurrent, len(active_devices))
            await asyncio.sleep(0.1)  # Simulate I/O
            active_devices.remove(device_id)
            return b'OK\r'

        # Create 3 mock devices with different connections
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
            client = DeviceClientAsync(model, mock_conn, event_loop)
            clients.append(client)

        # Send commands to all devices concurrently
        tasks = [
            clients[0].send_raw(b'CMD1\r', wait_for_response=True),
            clients[1].send_raw(b'CMD2\r', wait_for_response=True),
            clients[2].send_raw(b'CMD3\r', wait_for_response=True),
        ]

        await asyncio.gather(*tasks)

        # Verify devices operated concurrently (max_concurrent should be 3)
        assert max_concurrent == 3, (
            f'Expected 3 devices concurrent, got {max_concurrent}'
        )

    async def test_send_receive_atomic(self, sample_device_definition, event_loop):
        """Verify send+receive is atomic (not interruptible)"""

        operation_states = []

        async def mock_send_with_receive(data, wait_for_response=False):
            """Mock send that simulates send+receive"""
            operation_states.append(f'send:{data.decode()}')
            await asyncio.sleep(0.05)
            if wait_for_response:
                operation_states.append(f'receive:{data.decode()}')
            return b'OK\r'

        mock_conn = AsyncMock()
        mock_conn.send = mock_send_with_receive
        mock_conn.is_async = Mock(return_value=True)

        model = DeviceModel('test_device', sample_device_definition)
        client = DeviceClientAsync(model, mock_conn, event_loop)

        # Send two commands that expect responses
        tasks = [
            client.send_raw(b'CMD1\r', wait_for_response=True),
            client.send_raw(b'CMD2\r', wait_for_response=True),
        ]

        await asyncio.gather(*tasks)

        # Verify send+receive are atomic (not interleaved)
        # Should be: send:CMD1, receive:CMD1, send:CMD2, receive:CMD2
        # NOT: send:CMD1, send:CMD2, receive:CMD1, receive:CMD2
        assert operation_states == [
            'send:CMD1\r',
            'receive:CMD1\r',
            'send:CMD2\r',
            'receive:CMD2\r',
        ]

    async def test_no_global_lock_exists(self, sample_device_definition, event_loop):
        """Verify there's no global lock blocking all devices"""

        # This test verifies the fix for the global async lock bug
        # If a global lock exists, this test will timeout or perform poorly

        start_times = {}
        end_times = {}

        async def mock_send_timed(device_id, data, wait_for_response=False):
            """Track timing of operations"""
            start_times[device_id] = asyncio.get_event_loop().time()
            await asyncio.sleep(0.2)  # 200ms operation
            end_times[device_id] = asyncio.get_event_loop().time()
            return b'OK\r'

        # Create 3 devices
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
            client = DeviceClientAsync(model, mock_conn, event_loop)
            clients.append(client)

        # Send commands concurrently
        start = asyncio.get_event_loop().time()
        await asyncio.gather(
            clients[0].send_raw(b'CMD\r'),
            clients[1].send_raw(b'CMD\r'),
            clients[2].send_raw(b'CMD\r'),
        )
        total_time = asyncio.get_event_loop().time() - start

        # With concurrent execution: ~200ms total
        # With global lock (serialized): ~600ms total
        assert total_time < 0.4, (
            f'Operations took {total_time:.2f}s, suggesting global lock exists'
        )

        # Verify operations overlapped
        # Device 0 should start before device 2 finishes
        assert start_times[0] < end_times[2]


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
