"""
Supported for a YAML based device model definitions library
"""

import logging
from abc import ABC
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml

from .base import DeviceModelLibraryBase, DeviceModelSummary
from .model import DeviceModel

# TODO: investigate CUE (validation) or PKL as replacement/enhancements
# NOTE: DO NOT USE Pydantic since the validation mechanism should be cross-language

LOG = logging.getLogger(__name__)


def _load_yaml_file(path: str | Path) -> dict:
    try:
        file_path = Path(path) if isinstance(path, str) else path
        if file_path.is_file():
            with file_path.open() as stream:
                return yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        LOG.error(f'Failed reading YAML: path={path}', exc_info=exc)
    return {}


class YAMLDeviceModelLibrarySync(DeviceModelLibraryBase, ABC):
    """
    Synchronous implementation of YAML DeviceModelLibrary
    """

    def __init__(self, library_dirs: list[str]):
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

    def _all_library_yaml_files(self) -> list[Path]:
        yaml_files = []
        for path_str in self._dirs:
            path = Path(path_str)
            LOG.info(f'Looking for YAML model defs: path={path}')
            yaml_files.extend(path.rglob('*.yaml'))
        return yaml_files

    def supported_model_ids(self) -> frozenset[str]:
        if self._supported_model_ids:
            return self._supported_model_ids

        # build and cache the list of supported models based all the
        # yaml device definition files that are included in the library
        model_ids = [
            model_def_path.stem for model_def_path in self._all_library_yaml_files()
        ]
        self._supported_model_ids = frozenset(model_ids)  # immutable
        return self._supported_model_ids

    def supported_models(self) -> frozenset[DeviceModelSummary]:
        if self._supported_models:
            return self._supported_models

        supported_models = []
        for model_path in self._all_library_yaml_files():
            LOG.debug(f'Loading model: path={model_path}')
            if y := _load_yaml_file(model_path):
                model_id = model_path.stem
                if 'info' not in y:
                    LOG.error(f'Invalid file without info field: path={model_path}')
                    continue

                info = y['info']
                manufacturer = info.get('manufacturer', 'Unknown')

                for model_name in info.get('models', []):
                    LOG.debug(
                        f'Adding model: name={model_name}, manufacturer={manufacturer}'
                    )
                    supported_models.append(
                        DeviceModelSummary(manufacturer, model_name, model_id)
                    )

        self._supported_models = (
            supported_models  # frozenset(supported_models)  # immutable
        )
        return self._supported_models


class YAMLDeviceModelLibraryAsync(DeviceModelLibraryBase, ABC):
    """
    Asynchronous implementation of DeviceModelLibrary

    NOTE: For simplicity in initial implementation, decided to skip writing
    the asynchronous library and instead wrap the sync version for now.
    Especially since loading all the model files should be a rare occurrence.
    """

    def __init__(self, library_dirs: list[str], event_loop):
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
