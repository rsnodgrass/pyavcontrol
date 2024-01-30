#!/usr/bin/env python3
#
# Some examples of dynamic class generation
#   https://github.com/boto/boto3
#
# make sure that help(client) called on a client object actually shows documentation!
# show example of using ipython
#
# ``` python
# In [1]: from pyavcontrol import get_model, create_client
# In [2]: m = get_model('mcintosh_mx160')
# In [3] c = create_client(m)
# In [4]: c.
# c.mute       c.power
# c.volume
#
# In [5]: c.mute
# c.mute.on     c.mute.off
#
# In [6]: c.mute.on()
# ```

import logging
from dataclasses import dataclass
from typing import List

import coloredlogs

from pyavcontrol import DeviceClient, DeviceModelLibrary
from pyavcontrol.connection import NullConnection
from pyavcontrol.core import (
    camel_case,
    extract_named_regex,
    get_fstring_vars,
    missing_keys_in_dict,
    substitute_fstring_vars,
)
from pyavcontrol.helper import construct_synchronous_client

LOG = logging.getLogger(__name__)
coloredlogs.install(level="DEBUG")

# SendFunction = Callable[[list[int]], bool]


def main():
    url = "socket://localhost:4999"
    connection = NullConnection()

    library = DeviceModelLibrary.create()
    supported_models = library.supported_models()
    supported_models = ["mcintosh_mx160"]

    for model_id in supported_models:
        model_def = library.load_model(model_id)

        client = DeviceClient.create(model_def, connection)
        print(type(client))

        #        help(client)
        # print(client.software.info())

        #        help(client)
        # return


if __name__ == "__main__":
    main()
