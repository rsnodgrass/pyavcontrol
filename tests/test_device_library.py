import pytest

from pyavcontrol import DeviceModelLibrary

def test_default_library():
    library = DeviceModelLibrary.create()
    assert library
    assert len(library.supported_model_ids()) > 0
    assert len(library.supported_models()) > 0

def test_invalid_path():
    library = DeviceModelLibrary.create(library_dirs='/tmp/invalid_path_pyavcontrol')
    assert library
    assert len(library.supported_model_ids()) == 0
    assert len(library.supported_models()) == 0

if __name__ == "__main__":
    test_invalid_path()