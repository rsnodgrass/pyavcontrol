"""
Documentation support for generating Sphinx docs from device models.

This module loads all device models to ensure Sphinx documentation
picks up dynamically created classes.

NOTE: This should not be included in production code - it forces
all model definitions to be loaded for documentation purposes only.
"""

from __future__ import annotations

from pyavcontrol import DeviceClient
from pyavcontrol.connection import NullConnection
from pyavcontrol.library import DeviceModelLibrary

# models to include in documentation
MODELS: list[str] = [
    'hdfury_vrroom',
    'trinnov_altitude32',
    'lyngdorf_cd2',
    'mcintosh_mx160',
    'xantech_mx88_audio',
    'lyngdorf_tdai3400',
]

MODEL_DEFS: list = []
CLIENTS: list = []


def _load_models_for_docs() -> None:
    """Load all models and clients for documentation generation."""
    library = DeviceModelLibrary.create()

    for model_id in MODELS:
        model_def = library.load_model(model_id)
        if model_def:
            MODEL_DEFS.append(model_def)
            client = DeviceClient.create(model_def, NullConnection())
            CLIENTS.append(client)


# load on module import for Sphinx autodoc
_load_models_for_docs()
