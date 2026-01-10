"""Constants for pyavcontrol library."""

from pathlib import Path
from typing import Final

DEFAULT_ENCODING: Final[str] = 'ascii'
DEFAULT_EOL: Final[str] = '\r'
DEFAULT_TCP_IP_PORT: Final[int] = 4999  # IP2SL / Virtual IP2SL uses this port
DEFAULT_TIMEOUT: Final[float] = 1.0

PACKAGE_PATH: Final[Path] = Path(__file__).parent

PROCESSOR_TYPE: Final[str] = 'processor'
RECEIVER_TYPE: Final[str] = 'receiver'
MATRIX_TYPE: Final[str] = 'matrix'
ALL_DEVICE_TYPES: Final[list[str]] = [PROCESSOR_TYPE, RECEIVER_TYPE, MATRIX_TYPE]

DEFAULT_MODEL_LIBRARIES: Final[tuple[str, ...]] = (
    str(PACKAGE_PATH / 'data' / 'flattened'),
    str(PACKAGE_PATH / 'data' / 'src'),
    str(PACKAGE_PATH / 'data' / 'future'),
)

BAUD_RATES: Final[list[int]] = [
    2400, 4800, 9600, 14400, 19200, 38400, 57600, 115200, 128000, 256000
]
