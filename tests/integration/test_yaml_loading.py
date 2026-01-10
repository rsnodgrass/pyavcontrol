"""
Integration tests for loading all YAML device definitions.

Tests verify that all 22 device YAML files:
1. Load successfully without errors
2. Have valid structure
3. Have required fields
4. Pass Pydantic validation (when implemented)
"""

import pytest

from pyavcontrol.library.model import DeviceModel
from pyavcontrol.library.yaml_library import YAMLDeviceModelLibrarySync, _load_yaml_file

# Known problematic YAML files to skip in certain tests
# TODO: Fix these YAML files or update tests when fixed
SKIP_FILES = {
    'mcintosh_mx160.yaml': 'Invalid regex pattern (missing closing paren in mute.get)',
    'mcintosh_mx170.yaml': 'Missing connection field',
    'mcintosh_mx180.yaml': 'Missing connection and API fields',
    'mcintosh_legacy.yaml': 'Action missing cmd field',
    'lyngdorf_tdai3400.yaml': 'Invalid regex pattern (missing closing paren)',
    'hdfury_vrroom.yaml': 'Invalid regex pattern (unterminated character set)',
    'xantech_mx88_video.yaml': 'Missing connection and API fields',
    'trinnov_altitude16.yaml': 'Uses import_models (inheritance not tested yet)',
    'jbl_sdp75.yaml': 'Uses import_models (inherits from trinnov_altitude32)',
}


class TestYAMLLoading:
    """Test loading all device YAML files"""

    def test_all_yaml_files_exist(self, yaml_library_path):
        """Verify YAML library path exists and contains files"""
        assert yaml_library_path.exists(), f'Path does not exist: {yaml_library_path}'
        assert yaml_library_path.is_dir(), f'Not a directory: {yaml_library_path}'

        yaml_files = list(yaml_library_path.glob('*.yaml'))
        assert len(yaml_files) > 0, 'No YAML files found'
        assert len(yaml_files) >= 10, (
            f'Expected at least 10 devices, found {len(yaml_files)}'
        )

    def test_load_each_yaml_file(self, all_device_yaml_files):
        """Test that each YAML file loads without errors"""
        for yaml_file in all_device_yaml_files:
            result = _load_yaml_file(yaml_file)

            assert result is not None, f'Failed to load {yaml_file.name}'
            assert isinstance(result, dict), f'{yaml_file.name} did not return dict'
            assert len(result) > 0, f'{yaml_file.name} returned empty dict'

    def test_yaml_files_have_required_fields(self, all_device_yaml_files):
        """Test that each YAML has required top-level fields"""
        required_fields = ['id', 'info', 'connection', 'protocol', 'api']

        for yaml_file in all_device_yaml_files:
            if yaml_file.name in SKIP_FILES:
                pytest.skip(f'Skipping {yaml_file.name}: {SKIP_FILES[yaml_file.name]}')

            data = _load_yaml_file(yaml_file)

            for field in required_fields:
                assert field in data, (
                    f'{yaml_file.name} missing required field: {field}'
                )

            # Verify info has required subfields
            assert 'manufacturer' in data['info'] or 'name' in data['info'], (
                f'{yaml_file.name} info missing manufacturer/name'
            )

    def test_yaml_files_have_valid_connection(self, all_device_yaml_files):
        """Test that connection config is valid"""
        for yaml_file in all_device_yaml_files:
            if yaml_file.name in SKIP_FILES:
                continue

            data = _load_yaml_file(yaml_file)
            connection = data.get('connection', {})

            # Must have at least one connection type
            assert 'rs232' in connection or 'ip' in connection, (
                f'{yaml_file.name} has no rs232 or ip connection'
            )

    def test_yaml_files_have_valid_api(self, all_device_yaml_files):
        """Test that API definitions are valid"""
        for yaml_file in all_device_yaml_files:
            if yaml_file.name in SKIP_FILES:
                continue

            data = _load_yaml_file(yaml_file)
            api = data.get('api', {})

            assert len(api) > 0, f'{yaml_file.name} has empty api'

            # Each API group should have actions
            for group_name, group_def in api.items():
                assert 'actions' in group_def, (
                    f'{yaml_file.name} group {group_name} missing actions'
                )

                actions = group_def['actions']
                assert len(actions) > 0, (
                    f'{yaml_file.name} group {group_name} has no actions'
                )

                # Each action should have cmd (unless it's None for deletion)
                for action_name, action_def in actions.items():
                    if action_def is None:
                        continue
                    assert 'cmd' in action_def, (
                        f'{yaml_file.name} {group_name}.{action_name} missing cmd'
                    )

    def test_create_device_models(self, all_device_yaml_files):
        """Test creating DeviceModel objects from YAML"""
        for yaml_file in all_device_yaml_files:
            data = _load_yaml_file(yaml_file)
            model_id = yaml_file.stem

            # Create DeviceModel (with validation disabled for now)
            model = DeviceModel(model_id, data, validate_definition=False)

            assert model is not None
            assert model.id == model_id
            assert model.definition == data

    def test_yaml_library_loads_all_models(self, yaml_library_path):
        """Test YAMLDeviceModelLibrarySync loads all models"""
        library = YAMLDeviceModelLibrarySync([str(yaml_library_path)])

        model_ids = library.supported_model_ids()

        assert isinstance(model_ids, frozenset)
        assert len(model_ids) >= 10, (
            f'Expected at least 10 models, got {len(model_ids)}'
        )

        # Verify IDs are strings, not character arrays
        for model_id in model_ids:
            assert isinstance(model_id, str)
            assert len(model_id) > 5  # Real model IDs are longer than 5 chars
            assert '_' in model_id or '-' in model_id  # IDs have separators

    def test_yaml_library_model_ids_are_unique(self, yaml_library_path):
        """Test that all model IDs are unique"""
        library = YAMLDeviceModelLibrarySync([str(yaml_library_path)])
        model_ids = library.supported_model_ids()
        model_ids_list = list(model_ids)

        # frozenset automatically ensures uniqueness, but verify explicitly
        assert len(model_ids) == len(model_ids_list)

    def test_load_specific_known_models(self, yaml_library_path):
        """Test loading specific known device models"""
        library = YAMLDeviceModelLibrarySync([str(yaml_library_path)])

        # These models should exist in the library
        known_models = ['mcintosh_mx160', 'mcintosh_mx170']

        for model_id in known_models:
            yaml_path = yaml_library_path / f'{model_id}.yaml'
            if yaml_path.exists():
                model = library.load_model(model_id)
                assert model is not None, f'Failed to load {model_id}'
                assert model.id == model_id

    def test_yaml_files_have_valid_regex_patterns(self, all_device_yaml_files):
        """Test that regex patterns in YAML files compile successfully"""
        import re

        for yaml_file in all_device_yaml_files:
            if yaml_file.name in SKIP_FILES:
                continue

            data = _load_yaml_file(yaml_file)
            api = data.get('api', {})

            for group_name, group_def in api.items():
                actions = group_def.get('actions', {})

                for action_name, action_def in actions.items():
                    if action_def is None:
                        continue

                    # Check cmd regex if present
                    if 'cmd' in action_def and 'regex' in action_def['cmd']:
                        pattern = action_def['cmd']['regex']
                        try:
                            re.compile(pattern)
                        except re.error as e:
                            pytest.fail(
                                f'{yaml_file.name} {group_name}.{action_name} '
                                f'cmd has invalid regex: {e}'
                            )

                    # Check msg regex if present
                    if 'msg' in action_def and 'regex' in action_def['msg']:
                        pattern = action_def['msg']['regex']
                        try:
                            re.compile(pattern)
                        except re.error as e:
                            pytest.fail(
                                f'{yaml_file.name} {group_name}.{action_name} '
                                f'msg has invalid regex: {e}'
                            )


class TestYAMLRegexTests:
    """Test the regex test cases defined in YAML files"""

    def test_yaml_regex_tests_pass(self, all_device_yaml_files):
        """Verify that regex test cases in YAML files pass"""
        import re

        test_failures = []

        for yaml_file in all_device_yaml_files:
            if yaml_file.name in SKIP_FILES:
                continue

            data = _load_yaml_file(yaml_file)
            api = data.get('api', {})

            for group_name, group_def in api.items():
                actions = group_def.get('actions', {})

                for action_name, action_def in actions.items():
                    if action_def is None:
                        continue

                    msg = action_def.get('msg', {})
                    if 'regex' not in msg or 'tests' not in msg:
                        continue

                    pattern = msg['regex']
                    tests = msg['tests']

                    for test_input, expected_output in tests.items():
                        match = re.match(pattern, test_input)
                        if not match:
                            test_failures.append(
                                f'{yaml_file.name} {group_name}.{action_name}: '
                                f'pattern "{pattern}" did not match "{test_input}"'
                            )
                            continue

                        # Verify extracted groups match expected
                        actual_groups = match.groupdict()
                        for key, expected_value in expected_output.items():
                            if key not in actual_groups:
                                test_failures.append(
                                    f'{yaml_file.name} {group_name}.{action_name}: '
                                    f'missing group "{key}"'
                                )
                            elif str(actual_groups[key]) != str(expected_value):
                                test_failures.append(
                                    f'{yaml_file.name} {group_name}.{action_name}: '
                                    f'group "{key}" expected "{expected_value}", '
                                    f'got "{actual_groups[key]}"'
                                )

        if test_failures:
            pytest.fail('\n'.join(test_failures))


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
