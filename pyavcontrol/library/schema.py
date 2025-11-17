from typing import Literal, Union

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

ALLOWED_BYTESIZES = Literal[FIVEBITS, SIXBITS, SEVENBITS, EIGHTBITS]
ALLOWED_PARITY = Literal[
    PARITY_NONE, PARITY_EVEN, PARITY_ODD, PARITY_MARK, PARITY_SPACE
]
ALLOWED_STOP_BITS = Literal[STOPBITS_ONE, STOPBITS_ONE_POINT_FIVE, STOPBITS_TWO]
ALLOWED_BAUD_RATES = Literal[
    2400, 4800, 9600, 14400, 19200, 38400, 57600, 115200, 128000, 256000
]
DeviceType = Literal['processor', 'receiver', 'matrix']


class Info(BaseModel):
    manufacturer: str
    model: str
    type: DeviceType = PROCESSOR_TYPE  # type: ignore[assignment]
    tested: bool | None


class RS232Connection(BaseModel):
    """RS232 serial connection configuration"""

    type: Literal['rs232'] = 'rs232'
    default_port: str = '/dev/ttyUSB0'  # e.g., '/dev/ttyUSB0', 'COM3'
    baudrate: ALLOWED_BAUD_RATES = 9600
    bytesize: ALLOWED_BYTESIZES = EIGHTBITS
    parity: ALLOWED_PARITY = PARITY_NONE
    stopbits: ALLOWED_STOP_BITS = STOPBITS_ONE
    timeout: float = DEFAULT_TIMEOUT
    encoding: str = DEFAULT_ENCODING
    min_time_between_commands: float = 0.25


class IPConnection(BaseModel):
    """TCP/IP network connection configuration"""

    type: Literal['ip'] = 'ip'
    default_host: str = '192.168.1.1'
    default_port: PositiveInt = DEFAULT_TCP_IP_PORT
    timeout: float = DEFAULT_TIMEOUT
    encoding: str = DEFAULT_ENCODING
    min_time_between_commands: float = 0.25


# Legacy connection model (for backward compatibility)
class Connection(BaseModel):
    rs232: 'RS232Connection | None' = None
    ip: 'IPConnection | None' = None


# Discriminated union for connection config
ConnectionConfig = Union[RS232Connection, IPConnection]


class Protocol(BaseModel):
    encoding: str = DEFAULT_ENCODING
    command_eol: str = '\r'
    message_eol: str = '\r'


class ActionCommand(BaseModel):
    fstring: str
    regex: str | None


class ActionMessage(BaseModel):
    regex: str | None
    tests: dict


class Action(BaseModel):
    description: str | None = 'unknown'
    cmd: ActionCommand
    msg: ActionMessage | None


# api.<group_name>.actions.<action_name>
class GroupDef(BaseModel):
    actions: dict[str, Action]  # <action_name> = {}


class ModelSchema(BaseModel):
    info: Info
    connection: Connection
    protocol: Protocol
    api: dict[str, GroupDef]  # <group_name> = GroupDef


# NOTE: printout with Model.schema_json()
