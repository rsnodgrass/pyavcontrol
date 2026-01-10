"""Configuration key definitions for pyavcontrol."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ConfigKeys:
    """Configuration key names used throughout the library."""

    api: str = 'api'
    baudrate: str = 'baudrate'
    clear_before_new_commands: str = 'clear_before_new_commands'
    command_eol: str = 'command_eol'
    command_separator: str = 'command_separator'
    description: str = 'description'
    encoding: str = 'encoding'
    id: str = 'id'
    message_eol: str = 'message_eol'
    min_time_between_commands: str = 'min_time_between_commands'
    model: str = 'model'
    name: str = 'name'
    protocol: str = 'protocol'
    serial_config: str = 'serial_config'
    timeout: str = 'timeout'
    urls: str = 'urls'


CONFIG = ConfigKeys()


class DynamicConfig:
    """
    Allows completely dynamic configuration from a dictionary.

    Attributes are set dynamically from dict keys, enabling access like:
        config = DynamicConfig({'host': 'example.com', 'port': 80})
        print(config.host, config.port)
    """

    __slots__ = ('_raw',)

    def __init__(self, conf: dict[str, Any]) -> None:
        if not isinstance(conf, dict):
            raise TypeError(f'dict expected, found {type(conf).__name__}')

        object.__setattr__(self, '_raw', conf)
        for key, value in conf.items():
            object.__setattr__(self, key, value)

    def __getattr__(self, name: str) -> Any:
        try:
            return self._raw[name]
        except KeyError as e:
            raise AttributeError(
                f"'{type(self).__name__}' has no attribute '{name}'"
            ) from e
