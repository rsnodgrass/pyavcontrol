# postpone eval of annotations (for DeviceClient type annotation)
from __future__ import annotations

import logging
from abc import ABC, abstractmethod

from ..config import CONFIG
from ..connection import DeviceConnection
from ..const import *  # noqa: F403
from ..core import (
    camel_case,
    generate_docs_for_action,
    missing_keys_in_dict,
    substitute_fstring_vars, get_args_for_command,
)
from ..library.model import DeviceModel

LOG = logging.getLogger(__name__)


class DynamicActions:
    """
    Dynamically created class representing a group of actions that can be called
    on a device.
    """

    def __init__(self, model_name, actions_def):
        self._model_name = model_name
        self._actions_def = actions_def


def _create_activity_group_class(
    client: DeviceClient,
    model: DeviceModel,
    group_name: str,
    actions_model: dict,
    cls_bases=None,
):
    """
    Create dynamic class that represents a group of activities for a specific
    DeviceClient. These are injected into the DeviceClient as properties that
    can be accessed by the caller.
    """
    # CamelCase the model+group to represent this dynamic class of action methods
    cls_name = camel_case(f'{model.id} {group_name}')
    if client.is_async:
        cls_name += 'Async'

    if not cls_bases:
        cls_bases = (DynamicActions,)
    cls_props = {}

    # dynamically add methods (and associated documentation) for each action
    for action_name, action_def in actions_model['actions'].items():
        # handle yamlfmt/yamlfix rewriting of "on" and "off" as YAML keys into bools
        if type(action_name) is bool:
            action_name = 'on' if action_name else 'off'

        # ClientAPIAction(group=group, name=action_name, definition=action_def)
        method = _create_action_method(
            client, cls_name, group_name, action_name, action_def
        )

        # FIXME: danger Will Robinson...potential exploits (need to explore how to filter out)
        method.__name__ = action_name
        method.__doc__ = generate_docs_for_action(action_name, action_def)

        cls_props[action_name] = method

    # return the new dynamic class that contains the above actions
    cls = type(cls_name, cls_bases, cls_props)
    return cls(model.id, actions_model['actions'])


def _inject_client_api(client: DeviceClient, model: DeviceModel):
    """
    Add a property at the top level of a DeviceClient class that exposes a
    group of actions that can be called. If none are specified in the
    model definition, the client is returned unchanged.
    """
    api = model.definition.get(CONFIG.api, {})
    for group_name, group_actions in api.items():
        if hasattr(type(client), group_name):
            raise RuntimeError(f'Injecting "{group_name}" failed as it already exists in {type(client)}')

        # LOG.debug(f'Adding property for group {group_name}')
        group_class = _create_activity_group_class(
            client, model, group_name, group_actions
        )
        setattr(type(client), group_name, group_class)

    return client

def _create_action_method(
    client: DeviceClient,
    cls_name: str,
    group_name: str,
    action_name: str,
    action_def: dict,
):
    """
    Creates a dynamic method that makes calls against the provided client using
    the command format for the given action definition.

    This returns an asynchronous method if an event_loop is provided, otherwise
    a synchronous method is returned by default. Calling code knows whether they
    instantiated a synchronous or asynchronous client.
    """
    # noinspection PyShadowingNames
    LOG = logging.getLogger(cls_name)
    required_args = get_args_for_command(action_def)
    wait_for_response = False
    # FIXME: need to also convert response back into dictionary!

    def _prepare_request(**kwargs):
        if missing_keys := missing_keys_in_dict(required_args, kwargs):
            err_msg = f'Call to {group_name}.{action_name} missing required keys {missing_keys}, skipping!'
            LOG.error(err_msg)
            raise ValueError(err_msg)

        if cmd := action_def.get('cmd'):
            if fstring := cmd.get('fstring'):
                request = substitute_fstring_vars(fstring, kwargs)
                return request.encode(client.encoding())
        return None

    # noinspection PyUnusedLocal
    def _activity_call_sync(self, **kwargs) -> None:
        """Synchronous version of making a client call"""
        if request := _prepare_request(**kwargs):
            return client.send_raw(request)
        LOG.warning(f'Failed to make request for {group_name}.{action_name}')

    # noinspection PyUnusedLocal
    async def _activity_call_async(self, **kwargs) -> None:
        """
        Asynchronous version of making a client call is used when an event_loop
        is provided. Calling code knows whether they instantiated a synchronous
        or asynchronous client.
        """
        if request := _prepare_request(**kwargs):
            # noinspection PyUnresolvedReferences
            return await client.send_raw(request)
        LOG.warning(f'Failed to make request for {group_name}.{action_name}')

    # return the async or sync version of the request method
    if client.is_async:
        return _activity_call_async
    return _activity_call_sync


class DeviceClient(ABC):
    """
    DeviceClientBase base class that defines operations allowed
    to control a device.
    """

    #def __new__(cls, *args, **kwargs):
    #    return super().__new__(cls)

    def __init__(self, model: DeviceModel, connection: DeviceConnection):
        super().__init__()
        self._model = model
        self._connection = connection

    def encoding(self) -> str:
        """
        :return: the bytes encoding format for requests/responses
        """
        return self._model.encoding

    @property
    def is_async(self):
        """
        :return: True if this client implementation is asynchronous (asyncio) versus synchronous.
        """
        return False


    #@abstractmethod
    #def send_command(self, group: str, action: str, **kwargs) -> None:
        #"""
        #Call a command by the group/action and args as defined in the
        #device's protocol yaml. E.g.
        #client.send_command(group, action, arg1=one, my_arg=my_arg)
        #"""
        #raise NotImplementedError()

    @abstractmethod
    def send_raw(self, data: bytes) -> None:
        """
        Allows sending a raw data to the device. Generally this should not
        be used except for testing, since all commands should be defined in
        the yaml protocol configuration. No response messages are supported.
        """
        raise NotImplementedError()

    # @abstractmethod
    def describe(self) -> dict:
        return self._model.definition

    # FIXME: should take:
    #   1. a model
    #   2. a connection
    #   3. whether asynchronous
    @classmethod
    def create(
        cls,
        model: DeviceModel,
        connection: DeviceConnection,
        event_loop=None,
    ) -> DeviceClient:
        """
        Creates a DeviceClient instance using the standard pyserial connection
        types supported by this library when given details about the model
        and connection url.

        NOTE: The model definition could be passed in from any source, though
        it is recommended to only use those from the DeviceClient library. That
        said, it MAY make sense to split the entire connection stuff into a more
        generalized library for serial/IP communication to legacy devices and
        have libraries in separate package that are domain specific.

        If an event_loop argument is passed in this will return the
        asynchronous implementation. By default, the synchronous interface
        is returned.

        :param model: DeviceModel
        :param connection: connection to the device
        :param event_loop: optionally to get an interface that can be used asynchronously, pass in an event loop

        :return an instance of DeviceControllerBase
        """
        LOG.debug(f'Connecting to {model.id} at {connection!r}')

        print("WHAT!!!")

        if event_loop:
            # lazy import the async client to avoid loading both sync/async
            from .async_client import DeviceClientAsync

            base_classes = (DeviceClientAsync,)
        else:
            from .sync_client import DeviceClientSync

            base_classes = (DeviceClientSync,)

        # dynamically create subclass
        class_name = camel_case(f'{model.id} Client')
        LOG.debug(f'Creating {class_name} client with {model.id} protocol API')

        dynamic_class = type(class_name, base_classes, {})
        print("FA")

        # if event_loop provided, return an asynchronous client; otherwise synchronous
        if event_loop:
            client = dynamic_class(model, connection, event_loop)
            print("FOO")
            print(client)
        else:
            client = dynamic_class(model, connection)

        client.__module__ = f'pyavcontrol.client.{model.id}'
        client.__qualname__ = f'{client.__module__}.{class_name}'

        # inject all the methods into the new dynamic class
        client = _inject_client_api(client, model)

        return client
