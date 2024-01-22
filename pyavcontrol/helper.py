"""
Provides a simple interface to construct and wire together all the appropriate
classes together for the common use case. More advanced clients that require
more advanced functionality can wire together the client, connection, model,
and/or library directly.
"""
import logging
from pyavcontrol import DeviceClient, DeviceModelLibrary

LOG = logging.getLogger(__name__)

async def construct_async_client(
    model_id: str, url: str, event_loop, connection_config: dict = None
) -> DeviceClient:
    """
    Construct an asynchronous client

    :param model_id: Model identifier for the device
    :param url: The pyserial compatible connection URL
    :param connection_config: pyserial configuration overrides (defaults come from for model_def)
    :param event_loop: (optional) event loop if an asynchronous client is desired
    """
    from pyavcontrol.connection.async_connection import AsyncDeviceConnection

    # load the model and settings for interacting with the device
    library = DeviceModelLibrary.create(event_loop=event_loop)
    model = await library.load_model(model_id)
    # FIXME: err handling

    # FIXME: need to load connection_config also from the model!?
    if not connection_config:
        connection_config = {}

    connection = AsyncDeviceConnection(url, connection_config, event_loop)

    # FIXME: how does this handle failed connections? retries? lazy connections? that can be
    # a wrapper around the DeviceConnection object.

    client = DeviceClient.create(model, connection)
    return client


def construct_synchronous_client(
    model_id: str, url: str, connection_config: dict = None
) -> DeviceClient:
    """
    Construct a synchronous client

    :param model_id: Model identifier for the device
    :param url: The pyserial compatible connection URL
    :param connection_config: pyserial configuration overrides (defaults come from for model_def)
    """
    from pyavcontrol.connection.sync_connection import SyncDeviceConnection

    # load the model and settings for interacting with the device
    library = DeviceModelLibrary.create()
    model_def = library.load_model(model_id)
    # FIXME: err handling

    # FIXME: need to load connection_config also from the model!?
    if not connection_config:
        connection_config = {}

    connection = SyncDeviceConnection(url, connection_config)

    # FIXME: how does this handle failed connections? retries? lazy connections? that can be
    # a wrapper around the DeviceConnection object.

    client = DeviceClient.create(model_def, connection)
    return client
