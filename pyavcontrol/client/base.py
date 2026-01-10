"""Base device client with dynamic API generation."""

from __future__ import annotations

import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from pyavcontrol.config import CONFIG
from pyavcontrol.connection import DeviceConnection
from pyavcontrol.library.model import DeviceModel
from pyavcontrol.utils import (
    camel_case,
    generate_docs_for_action,
    get_args_for_command,
    missing_keys_in_dict,
    substitute_fstring_vars,
)

if TYPE_CHECKING:
    from asyncio import AbstractEventLoop
    from collections.abc import Awaitable, Callable

LOG = logging.getLogger(__name__)


class DynamicActions:
    """
    Dynamically created class representing a group of actions.

    Actions are callable methods generated from device model definitions.
    """

    __slots__ = ('_model_name', '_group_actions')

    def __init__(self, model_name: str, group_actions_def: dict[str, Any]) -> None:
        self._model_name = model_name
        self._group_actions = group_actions_def


@dataclass(slots=True)
class ActionDef:
    """Definition of a device action with command and response specs."""

    group: str
    name: str
    definition: dict[str, Any]
    required_args: list[str] = field(default_factory=list)
    response_expected: bool = False


def _create_activity_group_class(
    client: DeviceClient,
    model: DeviceModel,
    group_name: str,
    group_actions: dict[str, Any],
) -> DynamicActions:
    """
    Create a dynamic class representing a group of device actions.

    Args:
        client: DeviceClient instance
        model: Device model definition
        group_name: Name of the action group
        group_actions: Dictionary of action definitions

    Returns:
        Instance of dynamically created action group class.
    """
    cls_props: dict[str, Any] = {}
    cls_bases = (DynamicActions,)

    cls_name = camel_case(f'{model.id} {group_name}')
    if client.is_async:
        cls_name += 'Async'

    for action_name, action_def in group_actions.items():
        # handle YAML formatting of on/off as booleans
        if isinstance(action_name, bool):
            action_name = 'on' if action_name else 'off'

        action = ActionDef(group_name, action_name, action_def)
        action.required_args = get_args_for_command(action.definition)
        action.response_expected = 'msg' in action_def

        method = _create_action_method(client, cls_name, action)
        method.__name__ = action_name
        method.__doc__ = generate_docs_for_action(action_name, action_def)

        cls_props[action_name] = method

    dynamic_class = type(cls_name, cls_bases, cls_props)
    return dynamic_class(model.id, group_actions)


def _inject_client_api(client: DeviceClient, model: DeviceModel) -> DeviceClient:
    """
    Inject action groups as properties on the client.

    Args:
        client: DeviceClient to enhance
        model: Device model with API definitions

    Returns:
        Enhanced client with action group properties.

    Raises:
        RuntimeError: If action group name conflicts with existing attribute
    """
    api = model.definition.get(CONFIG.api, {})

    for group_name, group_def in api.items():
        if hasattr(type(client), group_name):
            raise RuntimeError(
                f'Injecting "{group_name}" failed as it already exists in {type(client)}'
            )

        group_actions = group_def['actions']
        group_class = _create_activity_group_class(
            client, model, group_name, group_actions
        )
        setattr(type(client), group_name, group_class)

    return client


def _create_action_method(
    client: DeviceClient,
    cls_name: str,
    action: ActionDef,
) -> Callable[..., Any] | Callable[..., Awaitable[Any]]:
    """
    Create a method that executes an action against the device.

    Returns sync or async method based on client type.

    Args:
        client: DeviceClient instance
        cls_name: Name for the dynamic class (used in logging)
        action: Action definition

    Returns:
        Callable that executes the action.
    """
    action_log = logging.getLogger(cls_name)

    def _prepare_request(**kwargs: Any) -> bytes | None:
        if missing_keys := missing_keys_in_dict(action.required_args, kwargs):
            err_msg = (
                f'Call to {action.group}.{action.name} missing required '
                f'keys {missing_keys}, skipping!'
            )
            action_log.error(err_msg)
            raise ValueError(err_msg)

        if cmd := action.definition.get('cmd'):
            if fstring := cmd.get('fstring'):
                request = substitute_fstring_vars(fstring, kwargs)
                return request.encode(client.encoding())

        return None

    def _extract_vars_in_response(response: bytes) -> dict[str, str]:
        response_text = response.decode(client.encoding())

        if msg := action.definition.get('msg'):
            if regex := msg.get('regex'):
                if match := re.match(regex, response_text):
                    return match.groupdict()

        return {}

    def _activity_call_sync(self: Any, **kwargs: Any) -> dict[str, str] | None:
        """Synchronous action execution."""
        if request := _prepare_request(**kwargs):
            if response := client.send_raw(
                request, wait_for_response=action.response_expected
            ):
                return _extract_vars_in_response(response)
            return None
        action_log.warning(f'Failed to make request for {action.group}.{action.name}')
        return None

    async def _activity_call_async(self: Any, **kwargs: Any) -> dict[str, str] | None:
        """Asynchronous action execution."""
        if request := _prepare_request(**kwargs):
            if response := await client.send_raw(
                request, wait_for_response=action.response_expected
            ):
                return _extract_vars_in_response(response)
            return None
        action_log.warning(f'Failed to make request for {action.group}.{action.name}')
        return None

    if client.is_async:
        return _activity_call_async
    return _activity_call_sync


class DeviceClient(ABC):
    """
    Base class for device control clients.

    Provides common interface for communicating with A/V equipment
    and dynamically generates action methods from device model definitions.
    """

    __slots__ = ('_model', '_connection')

    def __init__(self, model: DeviceModel, connection: DeviceConnection) -> None:
        """
        Initialize device client.

        Args:
            model: Device model with protocol definitions
            connection: Connection to the device
        """
        self._model = model
        self._connection = connection

    def encoding(self) -> str:
        """
        Get encoding format for requests/responses.

        Returns:
            Character encoding string.
        """
        return self._model.encoding

    @property
    def is_async(self) -> bool:
        """
        Check if this client uses async operations.

        Returns:
            True if asynchronous, False otherwise.
        """
        return False

    @property
    def client(self) -> DeviceConnection:
        """
        Get the underlying connection.

        Returns:
            DeviceConnection instance.
        """
        return self._connection

    @property
    def is_connected(self) -> bool:
        """
        Check if client is connected to device.

        Returns:
            True if connected.
        """
        return True

    @abstractmethod
    def send_raw(
        self,
        data: bytes,
        wait_for_response: bool = False,
        return_raw: bool = False,
    ) -> bytes | None:
        """
        Send raw bytes to the device.

        Args:
            data: Bytes to send
            wait_for_response: Whether to wait for response
            return_raw: Whether to return raw response bytes

        Returns:
            Response bytes if wait_for_response is True.
        """

    @property
    def model(self) -> DeviceModel:
        """
        Get the device model.

        Returns:
            DeviceModel instance.
        """
        return self._model

    @classmethod
    def create(
        cls,
        model: DeviceModel,
        connection: DeviceConnection,
        event_loop: AbstractEventLoop | None = None,
    ) -> DeviceClient:
        """
        Create a DeviceClient instance.

        Dynamically generates a subclass with action methods based on
        the model definition. Returns async client if event_loop provided.

        Args:
            model: Device model definition
            connection: Connection to the device
            event_loop: Optional event loop for async operation

        Returns:
            Configured DeviceClient instance.
        """
        class_name = camel_case(f'{model.id} Client')
        LOG.debug(f'Connecting to {model.id} at {connection!r} (class={class_name})')

        if event_loop:
            from pyavcontrol.client.async_client import DeviceClientAsync

            dynamic_class = type(class_name, (DeviceClientAsync,), {})
            client = dynamic_class(model, connection, event_loop)
        else:
            from pyavcontrol.client.sync_client import DeviceClientSync

            dynamic_class = type(class_name, (DeviceClientSync,), {})
            client = dynamic_class(model, connection)

        client.__module__ = f'pyavcontrol.client.{model.id}'
        client.__qualname__ = f'{client.__module__}.{class_name}'

        return _inject_client_api(client, model)
