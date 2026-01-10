"""Helper functions for constructing device clients."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from pyavcontrol.client.base import DeviceClient
from pyavcontrol.library import DeviceModelLibrary

if TYPE_CHECKING:
    from asyncio import AbstractEventLoop

LOG = logging.getLogger(__name__)


async def construct_async_client(
    model_id: str,
    url: str,
    event_loop: AbstractEventLoop,
    connection_config: dict[str, Any] | None = None,
) -> DeviceClient:
    """
    Construct an asynchronous device client.

    Args:
        model_id: Model identifier for the device
        url: pyserial-compatible connection URL
        event_loop: Event loop for async operations
        connection_config: Optional pyserial configuration overrides

    Returns:
        Configured async DeviceClient instance.
    """
    from pyavcontrol.connection.async_connection import AsyncDeviceConnection

    library = DeviceModelLibrary.create(event_loop=event_loop)
    model = await library.load_model(model_id)

    if model is None:
        raise ValueError(f"Model '{model_id}' not found in library")

    if connection_config is None:
        connection_config = {}

    connection = AsyncDeviceConnection(url, connection_config, event_loop)
    return DeviceClient.create(model, connection, event_loop=event_loop)


def construct_synchronous_client(
    model_id: str,
    url: str,
    connection_config: dict[str, Any] | None = None,
) -> DeviceClient:
    """
    Construct a synchronous device client.

    Args:
        model_id: Model identifier for the device
        url: pyserial-compatible connection URL
        connection_config: Optional pyserial configuration overrides

    Returns:
        Configured sync DeviceClient instance.

    Raises:
        ValueError: If model not found in library
    """
    from pyavcontrol.connection.sync_connection import SyncDeviceConnection

    library = DeviceModelLibrary.create()
    model = library.load_model(model_id)

    if model is None:
        raise ValueError(f"Model '{model_id}' not found in library")

    if connection_config is None:
        connection_config = {}

    connection = SyncDeviceConnection(url, connection_config)
    return DeviceClient.create(model, connection)
