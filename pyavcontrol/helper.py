"""
Provides a simple interface to construct and wire together all the appropriate
classes together for the common use case. More advanced clients that require
more advanced functionality can wire together the client, connection, model,
and/or library directly.
"""
from pyavcontrol import DeviceClient, DeviceModelLibrary


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

    if not connection_config:
        connection_config = {}

    library = DeviceModelLibrary.create(event_loop=event_loop)
    model = await library.load_model(model_id)
    # FIXME: err handling

    from pyavcontrol.connection.async_connection import AsyncDeviceConnection

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
    if not connection_config:
        connection_config = {}

    # load the model
    library = DeviceModelLibrary.create()
    model_def = library.load_model(model_id)
    # FIXME: err handling

    from pyavcontrol.connection.sync_connection import SyncDeviceConnection

    connection = SyncDeviceConnection(url, connection_config)

    # FIXME: how does this handle failed connections? retries? lazy connections? that can be
    # a wrapper around the DeviceConnection object.

    client = DeviceClient.create(model_def, connection)
    return client
