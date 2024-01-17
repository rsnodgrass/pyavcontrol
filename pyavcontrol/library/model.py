import logging

LOG = logging.getLogger(__name__)


class DeviceModel:
    def __init__(self, model_id: str, definition: dict, validate_definition=True):
        self._model_id = model_id
        self._definition = definition

        if validate_definition and not self.validate():
            raise ValueError(f'Invalid definition for model {model_id}')

    @property
    def encoding(self) -> str:
        return 'ascii'  # FIXME

    @property
    def id(self) -> str:
        """
        returns the unique identifier for this model definition
        """
        return self._model_id

    @property
    def definition(self) -> dict:
        """
        returns the raw definition for this model
        """
        return self._definition

    def validate(self) -> bool:
        """
        Validate the device model data structure using pydantic (allows multiple physical representations
        such as YAML/JSON/etc to be read in in the future).
        """
        if not DeviceModel.validate_model_definition(self._definition):
            LOG.warning(f'Error in model {self._model_id} definition')

        # FIXME: implement actual validation
        return True

    @staticmethod
    def validate_model_definition(model_def: dict) -> bool:
        """
        Validate that the given device model definition is valid
        """
        model_id = model_def.get('id', 'unknown')
        #        name = model_def.get("name")
        #        if not name:
        #            LOG.warning(f"Model '{model_id}' is missing required 'name'")
        #            return False

        # FIXME
        # LOG.warning(f"Model {name} fails validation: ...")
        return True
