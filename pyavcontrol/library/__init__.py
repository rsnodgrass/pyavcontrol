import re
from abc import abstractmethod, ABC
from dataclasses import dataclass
from pyavcontrol.const import DEFAULT_MODEL_LIBRARIES
from pyavcontrol.library.model import DeviceModel
from pyavcontrol.library.yaml_library import YAMLDeviceModelLibrarySync, YAMLDeviceModelLibraryAsync


@dataclass
class DeviceModelSummary:
    manufacturer: str
    model_name: str
    model_id: str

class DeviceModelLibrary(ABC):
    @abstractmethod
    def load_model(self, name: str) -> DeviceModel | None:
        """
        :param name: model id or a complete path to a file
        """
        raise NotImplementedError('Subclass must implement!')

    @abstractmethod
    def supported_model_ids(self) -> frozenset[str]:
        """
        :return: all model ids supported by this library
        """
        raise NotImplementedError('Subclass must implement!')

    @abstractmethod
    def supported_models(self) -> frozenset[DeviceModelSummary]:
        """
        NOTE: Subclasses may want to implement a more efficient mechanism than
        reading all the individual model definition files.

        :return: dict of all manufacturer + model names -> model_ids (e.g. 'McIntosh MX160' -> mcintosh_mx160)
        """
        raise NotImplementedError('Subclass must implement!')

    @staticmethod
    def create(library_dirs=DEFAULT_MODEL_LIBRARIES, event_loop=None):
        """
        Create an DeviceModelLibrary object representing all the complete
        library for resolving models and includes.

        If an event_loop argument is passed in this will return the
        asynchronous implementation. By default the synchronous interface
        is returned.

        :param library_dirs: paths used to resolve model names and includes (default=pyavcontrol's library)
        :param event_loop: to get an interface that can be used asynchronously, pass in an event loop

        :return an instance of DeviceLibraryModel
        """

        # NOTE: This is currently hardcoded to the YAML style libraries. May want to explore converting
        # this to Apple PKL instead, since that is more in line of the spirit of what model definitions are.
        if event_loop:
            return YAMLDeviceModelLibraryAsync(library_dirs, event_loop)
        return YAMLDeviceModelLibrarySync(library_dirs)


def filter_models_by_regex(models: set[DeviceModelSummary], regex: str) -> set[DeviceModelSummary]:
    """
    :return: dict of model summaries where the manufacturer or model name matches the
    provided regular expression
    """
    matches = set()
    rg = re.compile(regex)
    for summary in models:
        if rg.match(summary.manufacturer) or rg.match(summary.model_name) or rg.match(summary.model_id):
            matches += summary
    return matches