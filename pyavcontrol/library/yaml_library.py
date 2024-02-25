"""
Supported for a YAML based device model definitions library
"""
import logging
import os
import pathlib
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from typing import List, Set

import yaml

from . import DeviceModelSummary
from .. import DeviceModelLibrary
from ..const import DEFAULT_MODEL_LIBRARIES
from .model import DeviceModel

LOG = logging.getLogger(__name__)

def _load_yaml_file(path: str) -> dict:
    try:
        if pathlib.Path(path).is_file():
            with open(path) as stream:
                return yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        LOG.error(f'Failed reading YAML {path}: {exc}')
    return {}


class YAMLDeviceModelLibrarySync(DeviceModelLibrary, ABC):
    """
    Synchronous implementation of YAML DeviceModelLibrary
    """

    def __init__(self, library_dirs: List[str]):
        self._dirs = library_dirs
        self._supported_model_ids = None
        self._supported_models = None

    def load_model(self, model_id: str) -> DeviceModel | None:
        if '/' in model_id:
            LOG.error(f"Invalid model '{model_id}': cannot contain / in identifier")

        model_def = None
        for path in self._dirs:
            model_file = f'{path}/{model_id}.yaml'
            model_def = _load_yaml_file(model_file)
            if model_def:
                break

        if not model_def:
            LOG.warning(f"Could not find model '{model_id}' in the library")
            return None

        model = DeviceModel(model_id, model_def)
        return model

    def supported_model_ids(self) -> frozenset[str]:
        if self._supported_model_ids:
            return self._supported_model_ids

        # build and cache the list of supported models based all the
        # yaml device definition files that are included in the library
        supported_models = {}
        for path in self._dirs:
            for root, dirs, filenames in os.walk(path):
                for fn in filenames:
                    if fn.endswith('.yaml'):
                        model_file = os.path.join(root, fn)
                        name = pathlib.Path(model_file).stem
                        supported_models[name] = model_file

        self._supported_model_ids = frozenset(supported_models.keys()) # immutable
        return self._supported_model_ids

    def _read_model_names(self, filename: str) -> [str]:
        y = _load_yaml_file(filename)
        manufacturer = y.info.get('manufacturer', 'Unknown')

        model_names = []
        for model_name in y.info.get('models', []):
            model_names.append(model_name)
        if not model_names:
            LOG.warning(f"{filename} does not specify any supported model names")

        return (manufacturer, model_names)


    def supported_models(self) -> frozenset[DeviceModelSummary]:
        if self._supported_models:
            return self._supported_models

        supported_models = []
        for path in self._dirs:
            for root, dirs, filenames in os.walk(path):
                for fn in filenames:
                    if fn.endswith('.yaml'):
                        model_file = os.path.join(root, fn)
                        model_id = pathlib.Path(model_file).stem
                        (manufacturer, model_names) = self._read_model_names(model_file)
                        for model_name in model_names:
                            supported_models += DeviceModelSummary(manufacturer,
                                                                   model_name,
                                                                   model_id)

        self._supported_models = frozenset(supported_models) # immutable
        return self._supported_models


class YAMLDeviceModelLibraryAsync(DeviceModelLibrary, ABC):
    """
    Asynchronous implementation of DeviceModelLibrary

    NOTE: For simplicity in initial implementation, skipped writing the
    asynchronous library and use the sync version for now. Especially
    since loading all the model files should be a rare occurrence).
    """

    def __init__(self, library_dirs: List[str], event_loop):
        self._loop = event_loop
        self._dirs = library_dirs
        self._executor = ThreadPoolExecutor(max_workers=2)

        # FUTURE: implement any actual async library
        self._sync = DeviceModelLibrarySync(library_dirs)

    async def load_model(self, name: str) -> DeviceModel | None:
        return await self._loop.run_in_executor(
            self._executor, self._sync.load_model, name
        )


    async def supported_model_names(self) -> frozenset[str]:
        return await self._loop.run_in_executor(
            self._executor, self._sync.supported_model_names
        )
