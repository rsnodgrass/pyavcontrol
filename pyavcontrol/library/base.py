import re
from abc import ABC, abstractmethod
from dataclasses import dataclass

from pyavcontrol.library.model import DeviceModel


@dataclass
class DeviceModelSummary:
    manufacturer: str
    model_name: str
    model_id: str


def filter_models_by_regex(
    models: set[DeviceModelSummary], regex: str
) -> set[DeviceModelSummary]:
    """
    Filter the provided set of DeviceModelSummary down into only the ones that
    match the given regular expression.

    Returns:
        dict of model summaries where the manufacturer or model name matches the
        provided regular expression.
    """
    matches = set()
    rg = re.compile(regex)
    for summary in models:
        if (
            rg.match(summary.manufacturer)
            or rg.match(summary.model_name)
            or rg.match(summary.model_id)
        ):
            matches += summary
    return matches


class DeviceModelLibraryBase(ABC):
    @abstractmethod
    def load_model(self, name: str) -> DeviceModel:  # FIXME | None:
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
