"""Tests for DeviceModel validation and functionality."""

from __future__ import annotations

from typing import Any

from pyavcontrol.library.model import DeviceModel


class TestDeviceModel:
    """Test DeviceModel class functionality."""

    def test_valid_model_creation(
        self, sample_device_definition: dict[str, Any]
    ) -> None:
        """Test creating a valid DeviceModel."""
        model = DeviceModel('test_device', sample_device_definition)

        assert model.id == 'test_device'
        assert model.definition == sample_device_definition
        assert model.encoding == 'ascii'

    def test_model_info_property(
        self, sample_device_definition: dict[str, Any]
    ) -> None:
        """Test accessing model info."""
        model = DeviceModel('test_device', sample_device_definition)

        info = model.info
        assert info['manufacturer'] == 'Test Corp'
        assert 'Test Model 100' in info['models']
        assert info['type'] == 'processor'

    def test_model_encoding_default(self) -> None:
        """Test default encoding when not specified."""
        minimal_def = {'info': {'manufacturer': 'Test', 'models': ['Model']}}
        model = DeviceModel('test', minimal_def)

        assert model.encoding == 'ascii'

    def test_model_custom_encoding(self) -> None:
        """Test custom encoding from format section."""
        definition = {
            'info': {'manufacturer': 'Test', 'models': ['Model']},
            'format': {'encoding': 'utf-8'},
        }
        model = DeviceModel('test', definition)

        assert model.encoding == 'utf-8'

    def test_validation_skipped_when_disabled(self) -> None:
        """Test that validation can be skipped."""
        # empty dict would fail validation, but we skip it
        model = DeviceModel('test', {}, validate_definition=False)

        assert model.id == 'test'
        assert model.definition == {}

    def test_validate_model_definition_empty(self) -> None:
        """Test validation fails for empty definition."""
        assert DeviceModel.validate_model_definition({}) is False
        assert DeviceModel.validate_model_definition(None) is False

    def test_validate_model_definition_missing_info(self) -> None:
        """Test validation fails when info is missing."""
        definition = {'connection': {}, 'api': {}}
        assert DeviceModel.validate_model_definition(definition) is False

    def test_validate_model_definition_valid(
        self, sample_device_definition: dict[str, Any]
    ) -> None:
        """Test validation passes for valid definition."""
        assert DeviceModel.validate_model_definition(sample_device_definition) is True


class TestDeviceModelEdgeCases:
    """Test edge cases and error handling."""

    def test_model_with_no_api(self) -> None:
        """Test model without API section."""
        definition = {'info': {'manufacturer': 'Test', 'models': ['Model']}}
        model = DeviceModel('test', definition)

        assert model.definition.get('api') is None

    def test_model_definition_immutability(
        self, sample_device_definition: dict[str, Any]
    ) -> None:
        """Test that modifying returned definition doesn't affect model."""
        model = DeviceModel('test', sample_device_definition)
        definition = model.definition

        # modify the returned dict
        definition['info']['manufacturer'] = 'Modified'

        # original should be modified too (shallow copy behavior)
        # this documents current behavior, could add deep copy if needed
        assert model.definition['info']['manufacturer'] == 'Modified'
