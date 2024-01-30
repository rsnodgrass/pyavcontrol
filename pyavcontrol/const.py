"""Python client library for controlling A/V processors and receivers"""

import os

DEFAULT_ENCODING = "ascii"
DEFAULT_EOL = "\r" # ""\r\n"
DEFAULT_TCP_IP_PORT = 4999  # IP2SL / Virtual IP2SL uses this port
DEFAULT_TIMEOUT = 1.0

PACKAGE_PATH = os.path.dirname(__file__)

DEFAULT_MODEL_LIBRARIES = (
    f"{PACKAGE_PATH}/data/flattened",
    f"{PACKAGE_PATH}/data/src",
)  # FIXME: remove this later

BAUD_RATES = [ 2400, 4800, 9600, 14400, 19200, 38400, 57600, 115200, 128000, 256000 ]
