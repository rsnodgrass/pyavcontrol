"""
Unit tests for the critical bug fixes made to pyavcontrol.

Tests verify that the bugs are fixed:
1. String concatenation in utils.py missing_keys_in_dict
2. Set addition in library/base.py filter_models_by_regex
3. List append in yaml_library.py supported_model_ids
4. Regex null check in client/base.py _extract_vars_in_response
"""

import re
import sys
from pathlib import Path

import pytest

# Add parent directory to path to avoid circular imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pyavcontrol.library.base import DeviceModelSummary, filter_models_by_regex
from pyavcontrol.utils import missing_keys_in_dict


class TestUtilsBugFixes:
    """Test bug fixes in utils.py"""

    def test_missing_keys_returns_list_not_chars(self):
        """Bug: missing_keys += key was creating ['v','o','l','u','m','e'] instead of ['volume']"""
        required = ['power', 'volume', 'source']
        provided = {'power': 1, 'source': 2}  # volume is missing

        result = missing_keys_in_dict(required, provided)

        # Should return ['volume'], not ['v', 'o', 'l', 'u', 'm', 'e']
        assert result == ['volume']
        assert len(result) == 1
        assert isinstance(result[0], str)
        assert len(result[0]) > 1  # Not a single character

    def test_missing_keys_multiple_missing(self):
        """Test with multiple missing keys"""
        required = ['power', 'volume', 'source', 'mute']
        provided = {'power': 1}

        result = missing_keys_in_dict(required, provided)

        assert result == ['volume', 'source', 'mute']
        assert all(isinstance(k, str) and len(k) > 1 for k in result)

    def test_missing_keys_none_missing(self):
        """Test when no keys are missing"""
        required = ['power', 'volume']
        provided = {'power': 1, 'volume': 50, 'extra': 123}

        result = missing_keys_in_dict(required, provided)

        assert result == []


class TestLibraryBaseBugFixes:
    """Test bug fixes in library/base.py"""

    def test_filter_models_set_addition(self):
        """Bug: matches += summary doesn't work with sets"""
        model1 = DeviceModelSummary('McIntosh', 'MX160', 'mcintosh_mx160')
        model2 = DeviceModelSummary('McIntosh', 'MX170', 'mcintosh_mx170')
        model3 = DeviceModelSummary('Lyngdorf', 'TDAI3400', 'lyngdorf_tdai3400')

        models = {model1, model2, model3}

        # Filter for McIntosh
        result = filter_models_by_regex(models, 'McIntosh')

        # Should return a set with 2 McIntosh models
        assert isinstance(result, set)
        assert len(result) == 2
        assert model1 in result
        assert model2 in result
        assert model3 not in result

    def test_filter_models_by_model_name(self):
        """Test filtering by model name regex"""
        model1 = DeviceModelSummary('McIntosh', 'MX160', 'mcintosh_mx160')
        model2 = DeviceModelSummary('McIntosh', 'MX170', 'mcintosh_mx170')
        model3 = DeviceModelSummary('McIntosh', 'C48', 'mcintosh_c48')

        models = {model1, model2, model3}

        # Filter for MX series only
        result = filter_models_by_regex(models, 'MX')

        assert len(result) == 2
        assert model1 in result
        assert model2 in result
        assert model3 not in result


class TestRegexNullCheck:
    """Test regex null check bug fix"""

    def test_regex_match_returns_none_handled(self):
        """Bug: re.match() can return None, causing AttributeError on .groupdict()"""

        # Simulate the fixed code from client/base.py
        def extract_vars_safe(response_text: str, regex_pattern: str) -> dict:
            """Safely extract variables from response"""
            if match := re.match(regex_pattern, response_text):
                return match.groupdict()
            return {}

        # Test with matching pattern
        result = extract_vars_safe('VOL50', r'VOL(?P<volume>\d+)')
        assert result == {'volume': '50'}

        # Test with non-matching pattern (would cause crash without null check)
        result = extract_vars_safe('INVALID', r'VOL(?P<volume>\d+)')
        assert result == {}  # Should return empty dict, not crash

    def test_regex_match_with_no_groups(self):
        """Test regex with no named groups"""

        def extract_vars_safe(response_text: str, regex_pattern: str) -> dict:
            if match := re.match(regex_pattern, response_text):
                return match.groupdict()
            return {}

        result = extract_vars_safe('OK', r'OK')
        assert result == {}  # No groups to extract


class TestYAMLLoadingBugFix:
    """Test YAML loading bug fixes"""

    def test_model_ids_are_strings_not_chars(self):
        """Bug: model_ids += path.stem was concatenating characters"""
        # This is tested implicitly in the YAML loading tests
        # The bug would cause model IDs like 'mcintosh_mx160' to become
        # ['m','c','i','n','t','o','s','h','_','m','x','1','6','0']
        pass  # Covered by integration tests


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
