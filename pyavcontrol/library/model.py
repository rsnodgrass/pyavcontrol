"""Device model representation."""

from __future__ import annotations

import logging
from typing import Any

from pyavcontrol.const import DEFAULT_ENCODING

LOG = logging.getLogger(__name__)


class DeviceModel:
    """
    Represents a device model definition.

    Contains all protocol information needed to communicate with
    a specific A/V device model including commands, responses, and
    connection parameters.
    """

    __slots__ = ('_model_id', '_definition')

    def __init__(
        self,
        model_id: str,
        definition: dict[str, Any],
        validate_definition: bool = True,
    ) -> None:
        """
        Initialize device model.

        Args:
            model_id: Unique identifier for this model
            definition: Full model definition dictionary
            validate_definition: Whether to validate the definition

        Raises:
            ValueError: If validation fails and validate_definition is True
        """
        self._model_id = model_id
        self._definition = definition

        if validate_definition and not self.validate():
            raise ValueError(f'Invalid definition for model {model_id}')

    @property
    def encoding(self) -> str:
        """
        Get the character encoding for this device.

        Returns:
            Encoding string (e.g. 'ascii', 'utf-8').
        """
        return self._definition.get('format', {}).get('encoding', DEFAULT_ENCODING)

    @property
    def id(self) -> str:
        """
        Get the unique model identifier.

        Returns:
            Model ID string.
        """
        return self._model_id

    @property
    def info(self) -> dict[str, Any]:
        """
        Get device information.

        Returns:
            Dictionary with manufacturer, model names, etc.
        """
        return self._definition.get('info', {})

    @property
    def definition(self) -> dict[str, Any]:
        """
        Get the complete model definition.

        Returns:
            Full definition dictionary.
        """
        return self._definition

    def validate(self) -> bool:
        """
        Validate the device model definition.

        Returns:
            True if valid, False otherwise.
        """
        if not DeviceModel.validate_model_definition(self._definition):
            LOG.warning(f'Error in model {self._model_id} definition')

        return True

    @staticmethod
    def validate_model_definition(model_def: dict[str, Any] | None) -> bool:
        """
        Validate a device model definition dictionary.

        Args:
            model_def: Model definition to validate

        Returns:
            True if valid, False otherwise.
        """
        if not model_def:
            return False

        # basic structure validation
        required_fields = ['info']
        for field in required_fields:
            if field not in model_def:
                LOG.warning(f"Model definition missing required field '{field}'")
                return False

        return True
