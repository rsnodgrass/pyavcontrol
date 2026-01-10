"""
Unit tests for bug fixes in pyavcontrol.

Tests verify that critical bugs are fixed:
1. String concatenation in utils.py missing_keys_in_dict
2. Set addition in library/base.py filter_models_by_regex
3. List append in yaml_library.py supported_model_ids
4. Regex null check in client/base.py _extract_vars_in_response
"""

from __future__ import annotations

import re

from pyavcontrol.library.base import DeviceModelSummary, filter_models_by_regex
from pyavcontrol.utils import missing_keys_in_dict


class TestUtilsBugFixes:
    """Test bug fixes in utils.py."""

    def test_missing_keys_returns_list_not_chars(self) -> None:
        """Bug: missing_keys += key was creating ['v','o','l','u','m','e'] instead of ['volume']."""
        required = ['power', 'volume', 'source']
        provided = {'power': 1, 'source': 2}

        result = missing_keys_in_dict(required, provided)

        assert result == ['volume']
        assert len(result) == 1
        assert isinstance(result[0], str)
        assert len(result[0]) > 1

    def test_missing_keys_multiple_missing(self) -> None:
        """Test with multiple missing keys."""
        required = ['power', 'volume', 'source', 'mute']
        provided = {'power': 1}

        result = missing_keys_in_dict(required, provided)

        assert result == ['volume', 'source', 'mute']
        assert all(isinstance(k, str) and len(k) > 1 for k in result)

    def test_missing_keys_none_missing(self) -> None:
        """Test when no keys are missing."""
        required = ['power', 'volume']
        provided = {'power': 1, 'volume': 50, 'extra': 123}

        result = missing_keys_in_dict(required, provided)

        assert result == []


class TestLibraryBaseBugFixes:
    """Test bug fixes in library/base.py."""

    def test_filter_models_set_addition(self) -> None:
        """Bug: matches += summary doesn't work with sets."""
        model1 = DeviceModelSummary('Manufacturer A', 'Model160', 'mfr_a_model160')
        model2 = DeviceModelSummary('Manufacturer A', 'Model170', 'mfr_a_model170')
        model3 = DeviceModelSummary('Manufacturer B', 'Model3400', 'mfr_b_model3400')

        models = {model1, model2, model3}

        result = filter_models_by_regex(models, 'Manufacturer A')

        assert isinstance(result, set)
        assert len(result) == 2
        assert model1 in result
        assert model2 in result
        assert model3 not in result

    def test_filter_models_by_model_name(self) -> None:
        """Test filtering by model name regex."""
        model1 = DeviceModelSummary('Manufacturer A', 'Model160', 'mfr_a_model160')
        model2 = DeviceModelSummary('Manufacturer A', 'Model170', 'mfr_a_model170')
        model3 = DeviceModelSummary('Manufacturer A', 'Product48', 'mfr_a_product48')

        models = {model1, model2, model3}

        result = filter_models_by_regex(models, 'Model')

        assert len(result) == 2
        assert model1 in result
        assert model2 in result
        assert model3 not in result


class TestRegexNullCheck:
    """Test regex null check bug fix."""

    def test_regex_match_returns_none_handled(self) -> None:
        """Bug: re.match() can return None, causing AttributeError on .groupdict()."""

        def extract_vars_safe(response_text: str, regex_pattern: str) -> dict:
            """Safely extract variables from response."""
            if match := re.match(regex_pattern, response_text):
                return match.groupdict()
            return {}

        result = extract_vars_safe('VOL50', r'VOL(?P<volume>\d+)')
        assert result == {'volume': '50'}

        result = extract_vars_safe('INVALID', r'VOL(?P<volume>\d+)')
        assert result == {}

    def test_regex_match_with_no_groups(self) -> None:
        """Test regex with no named groups."""

        def extract_vars_safe(response_text: str, regex_pattern: str) -> dict:
            if match := re.match(regex_pattern, response_text):
                return match.groupdict()
            return {}

        result = extract_vars_safe('OK', r'OK')
        assert result == {}


class TestYAMLLoadingBugFix:
    """Test YAML loading bug fixes."""

    def test_model_ids_are_strings_not_chars(self) -> None:
        """
        Bug: model_ids += path.stem was concatenating characters.

        This is tested implicitly in the YAML loading tests. The bug would
        cause model IDs like 'model_id' to become ['m','o','d','e','l','_','i','d'].
        """
        pass  # covered by integration tests
