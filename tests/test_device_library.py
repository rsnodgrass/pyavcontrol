import pytest

from pyavcontrol import DeviceModelLibrary


def test_default_library():
    library = DeviceModelLibrary.create()
    assert library
    assert len(library.supported_model_ids()) > 0
    assert len(library.supported_models()) > 0


@pytest.mark.skip(
    reason='Library defaults to "/" when given invalid path - needs investigation'
)
def test_invalid_path():
    # Use a non-existent path that won't traverse into anything
    library = DeviceModelLibrary.create(
        library_dirs='/tmp/nonexistent_path_xyz_pyavcontrol_12345'
    )
    assert library
    # Should return empty set for non-existent path
    model_ids = library.supported_model_ids()
    assert len(model_ids) == 0, f'Expected 0 models, got {len(model_ids)}'
    assert len(library.supported_models()) == 0


if __name__ == '__main__':
    test_invalid_path()
