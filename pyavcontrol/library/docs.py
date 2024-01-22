"""
This includes all models to ensure that Sphinx documentation picks up all the
dynamically created classes.

THIS SHOULD NOT BE INCLUDED IN PRODUCTION CODE, it is specifically to force
documentation to be generated.

# FIXME: for Sphinx docs we may need to get more creative
# see also https://stackoverflow.com/questions/44316745/how-to-autogenerate-python-documentation-using-sphinx-when-using-dynamic-classes
#
# one idea...generate pyavcontrol/clients/<model_name>/yaml_library.py  (or just model_name.py)
#   which creates the class for the client + action groups
# then Sphinx will be able to document as it actually loads the vclasses.

FIXME: We may want to move this to tools/ or docs/
"""
from . import DeviceModelLibrary
from .. import DeviceClient
from ..connection import NullConnection

MODELS = [
    "hdfury_vrroom",
    "trinnov_altitude32",
    "lyngdorf_cd2",
    "mcintosh_mx160",
    "xantech_mx88_audio",
    "lyngdorf_tdai3400",
]

MODEL_DEFS = []
CLIENTS = []

for model_id in MODELS:
    model_def = DeviceModelLibrary.create().load_model(model_id)
    MODEL_DEFS.append(model_def)

    client = DeviceClient.create(model_def, NullConnection())
    CLIENTS.append(client)
