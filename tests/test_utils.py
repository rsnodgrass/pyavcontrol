"""Tests for utility functions."""

from __future__ import annotations

import pytest

from pyavcontrol.utils import (
    camel_case,
    extract_named_regex,
    get_args_for_command,
    get_fstring_vars,
    get_vars_for_message,
    missing_keys_in_dict,
    substitute_fstring_vars,
)


class TestMissingKeysInDict:
    """Test missing_keys_in_dict function."""

    def test_no_missing_keys(self) -> None:
        """Test when all keys present."""
        required = ['a', 'b', 'c']
        data = {'a': 1, 'b': 2, 'c': 3}

        result = missing_keys_in_dict(required, data)

        assert result == []

    def test_some_missing_keys(self) -> None:
        """Test when some keys missing."""
        required = ['power', 'volume', 'source']
        data = {'power': 1}

        result = missing_keys_in_dict(required, data)

        assert result == ['volume', 'source']

    def test_all_missing_keys(self) -> None:
        """Test when all keys missing."""
        required = ['a', 'b']
        data = {'x': 1, 'y': 2}

        result = missing_keys_in_dict(required, data)

        assert result == ['a', 'b']

    def test_returns_list_not_chars(self) -> None:
        """Regression test: ensure we get list of strings, not characters."""
        required = ['volume']
        data = {}

        result = missing_keys_in_dict(required, data)

        # should be ['volume'], not ['v', 'o', 'l', 'u', 'm', 'e']
        assert result == ['volume']
        assert len(result) == 1
        assert len(result[0]) > 1


class TestExtractNamedRegex:
    """Test extract_named_regex function."""

    def test_extract_single_group(self) -> None:
        """Test extracting single named group."""
        pattern = r'VOL(?P<volume>\d+)'
        result = extract_named_regex(pattern)

        assert result == {'volume': r'\d+'}

    def test_no_groups(self) -> None:
        """Test pattern with no named groups."""
        pattern = r'OK\r'
        result = extract_named_regex(pattern)

        assert result == {}


class TestSubstituteFstringVars:
    """Test substitute_fstring_vars function."""

    def test_single_substitution(self) -> None:
        """Test single variable substitution."""
        template = 'VOL{volume}'
        values = {'volume': 50}

        result = substitute_fstring_vars(template, values)

        assert result == 'VOL50'

    def test_multiple_substitutions(self) -> None:
        """Test multiple variable substitution."""
        template = '{cmd}{zone}:{value}'
        values = {'cmd': 'VOL', 'zone': 1, 'value': 50}

        result = substitute_fstring_vars(template, values)

        assert result == 'VOL1:50'

    def test_missing_variable_raises(self) -> None:
        """Test that missing variable raises KeyError."""
        template = '{missing}'
        values = {}

        with pytest.raises(KeyError):
            substitute_fstring_vars(template, values)


class TestGetFstringVars:
    """Test get_fstring_vars function."""

    def test_single_var(self) -> None:
        """Test extracting single variable."""
        template = 'VOL{volume}'
        result = get_fstring_vars(template)

        assert result == ['volume']

    def test_multiple_vars(self) -> None:
        """Test extracting multiple variables."""
        template = '{cmd}{zone}:{value}'
        result = get_fstring_vars(template)

        assert result == ['cmd', 'zone', 'value']

    def test_no_vars(self) -> None:
        """Test template with no variables."""
        template = 'POWER ON'
        result = get_fstring_vars(template)

        assert result == []

    def test_format_specifiers_ignored(self) -> None:
        """Test that format specifiers are stripped."""
        template = '{value:02d}'
        result = get_fstring_vars(template)

        assert result == ['value']


class TestCamelCase:
    """Test camel_case function."""

    def test_simple_conversion(self) -> None:
        """Test basic camel case conversion."""
        result = camel_case('hello world')
        assert result == 'HelloWorld'

    def test_underscores(self) -> None:
        """Test conversion with underscores."""
        result = camel_case('hello_world')
        assert result == 'HelloWorld'

    def test_hyphens(self) -> None:
        """Test conversion with hyphens."""
        result = camel_case('hello-world')
        assert result == 'HelloWorld'

    def test_mixed_separators(self) -> None:
        """Test with mixed separators."""
        result = camel_case('hello_world-test')
        assert result == 'HelloWorldTest'

    def test_removes_special_chars(self) -> None:
        """Test that special characters are removed but case is preserved."""
        result = camel_case('hello@world!')
        # @ and ! are removed but word boundaries still capitalize
        assert result == 'HelloWorld'


class TestGetArgsForCommand:
    """Test get_args_for_command function."""

    def test_extracts_args(self) -> None:
        """Test extracting command arguments."""
        action_def = {'cmd': {'fstring': 'VOL{volume}'}}

        result = get_args_for_command(action_def)

        assert result == ['volume']

    def test_no_cmd(self) -> None:
        """Test action without cmd."""
        action_def = {'description': 'Test'}

        result = get_args_for_command(action_def)

        assert result == []

    def test_no_fstring(self) -> None:
        """Test cmd without fstring."""
        action_def = {'cmd': {'regex': 'OK'}}

        result = get_args_for_command(action_def)

        assert result == []


class TestGetVarsForMessage:
    """Test get_vars_for_message function."""

    def test_extracts_vars(self) -> None:
        """Test extracting message variables."""
        action_def = {'msg': {'regex': r'VOL(?P<volume>\d+)'}}

        result = get_vars_for_message(action_def)

        assert 'volume' in result

    def test_no_msg(self) -> None:
        """Test action without msg."""
        action_def = {'cmd': {'fstring': 'TEST'}}

        result = get_vars_for_message(action_def)

        assert result == {}

    def test_no_regex(self) -> None:
        """Test msg without regex."""
        action_def = {'msg': {'tests': {}}}

        result = get_vars_for_message(action_def)

        assert result == {}
