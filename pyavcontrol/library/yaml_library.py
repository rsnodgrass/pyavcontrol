"""
Supported for a YAML based device model definitions library
"""
import logging
import os
import pathlib
from abc import ABC
from concurrent.futures import ThreadPoolExecutor
from typing import List

import yaml

from . import DeviceModelSummary
from .. import DeviceModelLibrary
from .model import DeviceModel

# TODO: investigate CUE (validation) or PKL as replacement/enhancements
# NOTE: DO NOT USE Pydantic since the validation mechanism should be cross-language

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
            return None

        for path in self._dirs:
            if model_def := _load_yaml_file(f'{path}/{model_id}.yaml'):
                return DeviceModel(model_id, model_def)

        LOG.warning(f"Could not find model '{model_id}' in the YAML library")
        return None

    def _all_library_yaml_files(self) -> list[str]:
        yaml_files = []
        for path in self._dirs:
            for root, dirs, filenames in os.walk(path):
                for fn in filenames:
                    if fn.endswith('.yaml'):
                        yaml_files += os.path.join(root, fn)
        return yaml_files

    def supported_model_ids(self) -> frozenset[str]:
        if self._supported_model_ids:
            return self._supported_model_ids

        # build and cache the list of supported models based all the
        # yaml device definition files that are included in the library
        model_ids = []
        for model_def_filename in self._all_library_yaml_files():
            model_ids += pathlib.Path(model_def_filename).stem
        self._supported_model_ids = frozenset(model_ids)  # immutable
        return self._supported_model_ids

    def supported_models(self) -> frozenset[DeviceModelSummary]:
        if self._supported_models:
            return self._supported_models

        supported_models = []
        for model_filename in self._all_library_yaml_files():
            if y := _load_yaml_file(model_filename):
                model_id = pathlib.Path(model_filename).stem
                manufacturer = y.info.get('manufacturer', 'Unknown')

                for model_name in y.info.get('models', []):
                    supported_models += DeviceModelSummary(manufacturer, model_name, model_id)

        self._supported_models = frozenset(supported_models)  # immutable
        return self._supported_models


class YAMLDeviceModelLibraryAsync(DeviceModelLibrary, ABC):
    """
    Asynchronous implementation of DeviceModelLibrary

    NOTE: For simplicity in initial implementation, decided to skip writing
    the asynchronous library and instead wrap the sync version for now.
    Especially since loading all the model files should be a rare occurrence.
    """
    def __init__(self, library_dirs: List[str], event_loop):
        self._loop = event_loop
        self._dirs = library_dirs
        self._executor = ThreadPoolExecutor(max_workers=2)
        self._sync = YAMLDeviceModelLibrarySync(library_dirs)

    async def load_model(self, name: str) -> DeviceModel | None:
        return await self._loop.run_in_executor(
            self._executor, self._sync.load_model, name
        )

    async def supported_models(self) -> frozenset[str]:
        return await self._loop.run_in_executor(
            self._executor, self._sync.supported_models
        )

    async def supported_model_ids(self) -> frozenset[str]:
        return await self._loop.run_in_executor(
            self._executor, self._sync.supported_model_ids
        )
