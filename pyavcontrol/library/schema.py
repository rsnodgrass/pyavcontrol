from typing import Literal, Optional

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
    ALL_DEVICE_TYPES,
    BAUD_RATES,
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
ALLOWED_BAUD_RATES = Literal[tuple(BAUD_RATES)]


class Info(BaseModel):
    manufacturer: str
    model: str
    type: ALL_DEVICE_TYPES = PROCESSOR_TYPE
    tested: bool | None


class RS232(BaseModel):
    baudrate: ALLOWED_BAUD_RATES = 9600
    bytesize: ALLOWED_BYTESIZES = EIGHTBITS
    parity: ALLOWED_PARITY = PARITY_NONE
    stopbits: ALLOWED_STOP_BITS = STOPBITS_ONE

    timeout: float | None = DEFAULT_TIMEOUT  # pyserial read timeout
    encoding: str | None = DEFAULT_ENCODING
    min_time_between_commands: float | None = 0.25


class IP(BaseModel):
    host: str | None = 'localhost'
    port: PositiveInt = DEFAULT_TCP_IP_PORT
    timeout: float | None = DEFAULT_TIMEOUT
    encoding: str | None = DEFAULT_ENCODING
    min_time_between_commands: float | None = 0.25


class Connection(BaseModel):
    rs232: RS232 | None
    ip: IP | None


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
