from typing import Optional, Literal

from pydantic import BaseModel, ValidationError, PositiveInt
from pyserial import (
    FIVEBITS, SIXBITS, SEVENBITS, EIGHTBITS, PARITY_NONE, PARITY_EVEN, PARITY_ODD,
    PARITY_MARK, PARITY_SPACE, STOPBITS_ONE, STOPBITS_ONE_POINT_FIVE, STOPBITS_TWO
)

from pyavcontrol.const import DEFAULT_TIMEOUT, DEFAULT_TCP_IP_PORT, DEFAULT_ENCODING, BAUD_RATES, ALL_DEVICE_TYPES, \
    PROCESSOR_TYPE

ALL_BYTESIZES = Literal[FIVEBITS, SIXBITS, SEVENBITS, EIGHTBITS]
ALL_PARITY = Literal[PARITY_NONE, PARITY_EVEN, PARITY_ODD, PARITY_MARK, PARITY_SPACE]
ALL_STOP_BITS = Literal[STOPBITS_ONE, STOPBITS_ONE_POINT_FIVE, STOPBITS_TWO]

class Info(BaseModel):
    manufacturer: str
    model: str
    type: Literal[ALL_DEVICE_TYPES] = PROCESSOR_TYPE
    tested: Optional[bool]

class RS232(BaseModel):
    baudrate: Literal[BAUD_RATES] = 9600
    bytesize: Literal[ALL_BYTESIZES] = EIGHTBITS
    parity: ALL_PARITY = PARITY_NONE
    stopbits: ALL_STOP_BITS = STOPBITS_ONE

    timeout: Optional[float = DEFAULT_TIMEOUT  # pyserial read timeout
    encoding: Optional[str] = DEFAULT_ENCODING
    min_time_between_commands: Optional[float] = 0.25

class IP(BaseModel):
    host: Optional[str] = 'localhost'
    port: PositiveInt = DEFAULT_TCP_IP_PORT
    timeout: Optional[float] = DEFAULT_TIMEOUT
    encoding: Optional[str] = DEFAULT_ENCODING
    min_time_between_commands: Optional[float] = 0.25

class Connection(BaseModel):
    rs232: Optional[RS232]
    ip: Optional[IP]

class Protocol(BaseModel):
    encoding: str = DEFAULT_ENCODING
    command_eol: str = "\r"
    message_eol: str = "\r"

class ActionCommand(BaseModel):
    fstring: str
    regex: Optional[str]

class ActionMessage(BaseModel):
    regex: Optional[str]
    tests: dict

class Action(BaseModel):
    description: Optional[str] = 'unknown'
    cmd: ActionCommand
    msg: Optional[ActionMessage]

# api.<group_name>.actions.<action_name>
class GroupDef(BaseModel):
    actions: dict[str, Action] # <action_name> = {}

class ModelSchema(BaseModel):
    info: Info
    connection: Connection
    protocol: Protocol
    api: dict[str, GroupDef] # <group_name> = GroupDef

# NOTE: printout with Model.schema_json()
