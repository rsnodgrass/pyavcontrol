"""Pydantic schemas for device model validation."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, PositiveInt
from serial import (
    EIGHTBITS,
    FIVEBITS,
    PARITY_EVEN,
    PARITY_MARK,
    PARITY_NONE,
    PARITY_ODD,
    PARITY_SPACE,
    SEVENBITS,
    SIXBITS,
    STOPBITS_ONE,
    STOPBITS_ONE_POINT_FIVE,
    STOPBITS_TWO,
)

from pyavcontrol.const import (
    DEFAULT_ENCODING,
    DEFAULT_TCP_IP_PORT,
    DEFAULT_TIMEOUT,
    PROCESSOR_TYPE,
)

# type aliases for serial configuration
ByteSizeType = Literal[FIVEBITS, SIXBITS, SEVENBITS, EIGHTBITS]
ParityType = Literal[PARITY_NONE, PARITY_EVEN, PARITY_ODD, PARITY_MARK, PARITY_SPACE]
StopBitsType = Literal[STOPBITS_ONE, STOPBITS_ONE_POINT_FIVE, STOPBITS_TWO]
BaudRateType = Literal[
    2400, 4800, 9600, 14400, 19200, 38400, 57600, 115200, 128000, 256000
]
DeviceType = Literal['processor', 'receiver', 'matrix']


class Info(BaseModel):
    """Device information schema."""

    manufacturer: str
    model: str
    type: DeviceType = PROCESSOR_TYPE  # type: ignore[assignment]
    tested: bool | None = None

    model_config = {'extra': 'allow'}


class RS232Connection(BaseModel):
    """RS232 serial connection configuration."""

    type: Literal['rs232'] = 'rs232'
    default_port: str = '/dev/ttyUSB0'
    baudrate: int = 9600
    bytesize: int = EIGHTBITS
    parity: str = PARITY_NONE
    stopbits: float = STOPBITS_ONE
    timeout: float = DEFAULT_TIMEOUT
    encoding: str = DEFAULT_ENCODING
    min_time_between_commands: float = 0.25

    model_config = {'extra': 'allow'}


class IPConnection(BaseModel):
    """TCP/IP network connection configuration."""

    type: Literal['ip'] = 'ip'
    default_host: str = '192.168.1.1'
    default_port: PositiveInt = DEFAULT_TCP_IP_PORT
    timeout: float = DEFAULT_TIMEOUT
    encoding: str = DEFAULT_ENCODING
    min_time_between_commands: float = 0.25

    model_config = {'extra': 'allow'}


class Connection(BaseModel):
    """Connection configuration with optional RS232 and IP settings."""

    rs232: RS232Connection | None = None
    ip: IPConnection | None = None

    model_config = {'extra': 'allow'}


class Protocol(BaseModel):
    """Protocol format configuration."""

    encoding: str = DEFAULT_ENCODING
    command_eol: str = '\r'
    message_eol: str = '\r'

    model_config = {'extra': 'allow'}


class ActionCommand(BaseModel):
    """Command specification for an action."""

    fstring: str
    regex: str | None = None

    model_config = {'extra': 'allow'}


class ActionMessage(BaseModel):
    """Response message specification for an action."""

    regex: str | None = None
    tests: dict[str, dict[str, str | int]] | None = None

    model_config = {'extra': 'allow'}


class Action(BaseModel):
    """Device action definition."""

    description: str | None = 'unknown'
    cmd: ActionCommand
    msg: ActionMessage | None = None

    model_config = {'extra': 'allow'}


class GroupDef(BaseModel):
    """Action group definition."""

    actions: dict[str, Action | None]

    model_config = {'extra': 'allow'}


class ModelSchema(BaseModel):
    """Complete device model schema."""

    info: Info
    connection: Connection
    protocol: Protocol
    api: dict[str, GroupDef]

    model_config = {'extra': 'allow'}
