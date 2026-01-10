"""Tests for DeviceModelLibrary."""

from __future__ import annotations

from pathlib import Path

from pyavcontrol import DeviceModelLibrary
from pyavcontrol.library.base import DeviceModelSummary, filter_models_by_regex
from pyavcontrol.library.yaml_library import YAMLDeviceModelLibrarySync


class TestDeviceModelLibrary:
    """Test DeviceModelLibrary functionality."""

    def test_default_library_creation(self) -> None:
        """Test creating library with default paths."""
        library = DeviceModelLibrary.create()
        assert library is not None

    def test_library_has_models(self) -> None:
        """Test that library has some models."""
        library = DeviceModelLibrary.create()
        model_ids = library.supported_model_ids()

        assert len(model_ids) > 0

    def test_library_model_ids_are_strings(self) -> None:
        """Test that model IDs are proper strings, not character arrays."""
        library = DeviceModelLibrary.create()
        model_ids = library.supported_model_ids()

        for model_id in model_ids:
            assert isinstance(model_id, str)
            # real IDs are longer than 5 characters
            assert len(model_id) > 5

    def test_load_model_by_id(self) -> None:
        """Test loading a specific model."""
        library = DeviceModelLibrary.create()
        model_ids = library.supported_model_ids()

        if model_ids:
            # try to load the first available model
            model_id = next(iter(model_ids))
            model = library.load_model(model_id)

            assert model is not None
            assert model.id == model_id

    def test_load_nonexistent_model(self) -> None:
        """Test loading a model that doesn't exist."""
        library = DeviceModelLibrary.create()
        model = library.load_model('nonexistent_model_xyz_123')

        assert model is None

    def test_load_model_with_slash_fails(self) -> None:
        """Test that model ID with slash is rejected."""
        library = DeviceModelLibrary.create()
        model = library.load_model('invalid/model')

        assert model is None

    def test_supported_models_returns_summaries(self) -> None:
        """Test that supported_models returns DeviceModelSummary objects."""
        library = DeviceModelLibrary.create()
        models = library.supported_models()

        for summary in models:
            assert isinstance(summary, DeviceModelSummary)
            assert summary.manufacturer
            assert summary.model_name
            assert summary.model_id


class TestFilterModelsByRegex:
    """Test model filtering functionality."""

    def test_filter_by_manufacturer(self) -> None:
        """Test filtering by manufacturer name."""
        models = {
            DeviceModelSummary('Manufacturer A', 'Model 1', 'mfr_a_model1'),
            DeviceModelSummary('Manufacturer A', 'Model 2', 'mfr_a_model2'),
            DeviceModelSummary('Manufacturer B', 'Model 1', 'mfr_b_model1'),
        }

        result = filter_models_by_regex(models, 'Manufacturer A')

        assert len(result) == 2
        assert all(s.manufacturer == 'Manufacturer A' for s in result)

    def test_filter_by_model_name(self) -> None:
        """Test filtering by model name."""
        models = {
            DeviceModelSummary('Manufacturer', 'Model 100', 'model_100'),
            DeviceModelSummary('Manufacturer', 'Model 200', 'model_200'),
            DeviceModelSummary('Manufacturer', 'Product 300', 'product_300'),
        }

        result = filter_models_by_regex(models, 'Model')

        assert len(result) == 2

    def test_filter_by_model_id(self) -> None:
        """Test filtering by model ID."""
        models = {
            DeviceModelSummary('Manufacturer', 'Model', 'abc_model'),
            DeviceModelSummary('Manufacturer', 'Model', 'xyz_model'),
        }

        result = filter_models_by_regex(models, 'abc')

        assert len(result) == 1
        assert next(iter(result)).model_id == 'abc_model'

    def test_filter_returns_set(self) -> None:
        """Test that filter returns a set."""
        models: set[DeviceModelSummary] = set()
        result = filter_models_by_regex(models, 'test')

        assert isinstance(result, set)

    def test_filter_empty_set(self) -> None:
        """Test filtering empty set."""
        result = filter_models_by_regex(set(), 'test')
        assert len(result) == 0


class TestYAMLLibrary:
    """Test YAML-specific library functionality."""

    def test_yaml_library_sync_creation(self, yaml_library_path: Path) -> None:
        """Test creating sync YAML library."""
        library = YAMLDeviceModelLibrarySync([str(yaml_library_path)])

        assert library is not None
        model_ids = library.supported_model_ids()
        assert len(model_ids) > 0

    def test_yaml_files_exist(self, yaml_library_path: Path) -> None:
        """Test that YAML library path has files."""
        yaml_files = list(yaml_library_path.glob('*.yaml'))
        assert len(yaml_files) > 0
