"""YAML-based device model library implementation."""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

from pyavcontrol.library.base import DeviceModelLibraryBase, DeviceModelSummary
from pyavcontrol.library.model import DeviceModel

if TYPE_CHECKING:
    from asyncio import AbstractEventLoop

LOG = logging.getLogger(__name__)


def _load_yaml_file(path: str | Path) -> dict[str, Any]:
    """
    Load and parse a YAML file.

    Args:
        path: Path to the YAML file

    Returns:
        Parsed dictionary or empty dict on error.
    """
    try:
        file_path = Path(path) if isinstance(path, str) else path
        if file_path.is_file():
            with file_path.open() as stream:
                return yaml.safe_load(stream) or {}
    except yaml.YAMLError:
        LOG.exception(f'Failed reading YAML: path={path}')
    return {}


class YAMLDeviceModelLibrarySync(DeviceModelLibraryBase):
    """
    Synchronous YAML device model library.

    Loads device definitions from YAML files in specified directories.
    """

    __slots__ = ('_dirs', '_supported_model_ids', '_supported_models')

    def __init__(self, library_dirs: list[str]) -> None:
        """
        Initialize YAML library.

        Args:
            library_dirs: List of directory paths to search for YAML files
        """
        self._dirs = library_dirs
        self._supported_model_ids: frozenset[str] | None = None
        self._supported_models: list[DeviceModelSummary] | None = None

    def load_model(self, model_id: str) -> DeviceModel | None:
        """
        Load a device model by ID.

        Args:
            model_id: Model identifier (without .yaml extension)

        Returns:
            DeviceModel instance or None if not found.
        """
        if '/' in model_id:
            LOG.error(f"Invalid model '{model_id}': cannot contain / in identifier")
            return None

        for dir_path in self._dirs:
            yaml_path = Path(dir_path) / f'{model_id}.yaml'
            if model_def := _load_yaml_file(yaml_path):
                return DeviceModel(model_id, model_def)

        LOG.warning(f"Could not find model '{model_id}' in the YAML library")
        return None

    def _all_library_yaml_files(self) -> list[Path]:
        """
        Get all YAML files from library directories.

        Returns:
            List of Path objects for all .yaml files.
        """
        yaml_files: list[Path] = []

        for path_str in self._dirs:
            path = Path(path_str)
            LOG.info(f'Looking for YAML model defs: path={path}')
            try:
                yaml_files.extend(path.rglob('*.yaml'))
            except (TimeoutError, PermissionError, OSError) as e:
                LOG.warning(f'Skipping path due to error: path={path}, error={e}')
                continue

        return yaml_files

    def supported_model_ids(self) -> frozenset[str]:
        """
        Get all model IDs available in the library.

        Returns:
            Frozen set of model ID strings.
        """
        if self._supported_model_ids is not None:
            return self._supported_model_ids

        model_ids = [path.stem for path in self._all_library_yaml_files()]
        self._supported_model_ids = frozenset(model_ids)
        return self._supported_model_ids

    def supported_models(self) -> frozenset[DeviceModelSummary]:
        """
        Get summaries of all supported models.

        Returns:
            Frozen set of DeviceModelSummary objects.
        """
        if self._supported_models is not None:
            return frozenset(self._supported_models)

        supported_models: list[DeviceModelSummary] = []

        for model_path in self._all_library_yaml_files():
            LOG.debug(f'Loading model: path={model_path}')
            yaml_data = _load_yaml_file(model_path)

            if not yaml_data:
                continue

            if 'info' not in yaml_data:
                LOG.error(f'Invalid file without info field: path={model_path}')
                continue

            model_id = model_path.stem
            info = yaml_data['info']
            manufacturer = info.get('manufacturer', 'Unknown')

            for model_name in info.get('models', []):
                LOG.debug(
                    f'Adding model: name={model_name}, manufacturer={manufacturer}'
                )
                supported_models.append(
                    DeviceModelSummary(manufacturer, model_name, model_id)
                )

        self._supported_models = supported_models
        return frozenset(supported_models)


class YAMLDeviceModelLibraryAsync(DeviceModelLibraryBase):
    """
    Asynchronous YAML device model library.

    Wraps synchronous library for async contexts using thread executor.
    """

    __slots__ = ('_dirs', '_executor', '_loop', '_sync')

    def __init__(self, library_dirs: list[str], event_loop: AbstractEventLoop) -> None:
        """
        Initialize async YAML library.

        Args:
            library_dirs: List of directory paths to search
            event_loop: Event loop for async operations
        """
        self._loop = event_loop
        self._dirs = library_dirs
        self._executor = ThreadPoolExecutor(max_workers=2)
        self._sync = YAMLDeviceModelLibrarySync(library_dirs)

    async def load_model(self, name: str) -> DeviceModel | None:
        """
        Load a device model asynchronously.

        Args:
            name: Model identifier

        Returns:
            DeviceModel instance or None if not found.
        """
        return await self._loop.run_in_executor(
            self._executor, self._sync.load_model, name
        )

    async def supported_models(self) -> frozenset[DeviceModelSummary]:
        """
        Get all supported model summaries asynchronously.

        Returns:
            Frozen set of DeviceModelSummary objects.
        """
        return await self._loop.run_in_executor(
            self._executor, self._sync.supported_models
        )

    async def supported_model_ids(self) -> frozenset[str]:
        """
        Get all supported model IDs asynchronously.

        Returns:
            Frozen set of model ID strings.
        """
        return await self._loop.run_in_executor(
            self._executor, self._sync.supported_model_ids
        )
