"""Utility functions for pyavcontrol."""

import logging
import re
from typing import Any

LOG = logging.getLogger(__name__)

NAMED_REGEX_PATTERN = re.compile(r'\(\?P<(?P<name>.+)>(?P<regex>.+)\)')
FSTRING_ARG_PATTERN = re.compile(r'{(?P<arg_name>[^}:]+)(?::[^}]*)?}')


def extract_named_regex(text: str) -> dict[str, str]:
    """
    Parse out named regex patterns from text into a dictionary.

    Args:
        text: String containing named regex patterns like (?P<name>regex)

    Returns:
        Dictionary mapping group names to their regex patterns.
    """
    return {
        m.group('name'): m.group('regex') for m in NAMED_REGEX_PATTERN.finditer(text)
    }


def missing_keys_in_dict(required_keys: list[str], d: dict[str, Any]) -> list[str]:
    """
    Check that the provided dictionary contains all required keys.

    Args:
        required_keys: List of keys that must be present
        d: Dictionary to check

    Returns:
        List of missing keys (empty if all present).
    """
    return [key for key in required_keys if key not in d]


def substitute_fstring_vars(fstring: str, values: dict[str, Any]) -> str:
    """
    Substitute variables in an f-string template.

    Args:
        fstring: Template string with {variable} placeholders
        values: Dictionary of variable names to values

    Returns:
        String with variables substituted.
    """
    return fstring.format(**values)


def get_fstring_vars(text: str) -> list[str]:
    """
    Extract all f-string style variable names from the given string.

    Args:
        text: String containing {variable} placeholders

    Returns:
        List of variable names found in the template.
    """
    return [m.group('arg_name') for m in FSTRING_ARG_PATTERN.finditer(text)]


def camel_case(text: str) -> str:
    """
    Convert string into CamelCase format.

    Removes spaces and special characters, capitalizing word boundaries.

    Args:
        text: Input string with spaces, underscores, or hyphens

    Returns:
        CamelCase version of the string.
    """
    return re.sub('[^0-9a-zA-Z]+', '', re.sub('[-_.]+', ' ', text).title())


def get_subkey(
    dictionary: dict[str, Any],
    top_key: str,
    key: str,
    log_missing: bool = True,
) -> Any | None:
    """
    Load a subkey from a nested dictionary.

    Args:
        dictionary: The dictionary to search
        top_key: The top-level key
        key: The subkey to retrieve
        log_missing: Whether to log warning if key is missing

    Returns:
        The value or None if not found.
    """
    nested = dictionary.get(top_key)
    if not nested:
        if log_missing:
            LOG.warning(
                f"Missing top level key '{top_key}' for subkey '{key}'; returning None"
            )
        return None

    value = nested.get(key)
    if value is None and log_missing:
        LOG.warning(f"Missing subkey '{key}' under key '{top_key}'; returning None")
    return value


def get_vars_for_message(action_def: dict[str, Any]) -> dict[str, str]:
    """
    Parse out all variables returned in the msg response for this action.

    Args:
        action_def: Action definition dictionary

    Returns:
        Dictionary of variable names to their regex patterns.
    """
    if msg := action_def.get('msg'):
        if regex := msg.get('regex'):
            return extract_named_regex(regex)
    return {}


def get_args_for_command(action_def: dict[str, Any]) -> list[str]:
    """
    Parse the command definition into an array of arguments.

    Args:
        action_def: Action definition dictionary

    Returns:
        List of argument names for the command.
    """
    if cmd := action_def.get('cmd'):
        if fstring := cmd.get('fstring'):
            return get_fstring_vars(fstring)
    return []


def generate_docs_for_action(action_name: str, action_def: dict[str, Any]) -> str:
    """
    Generate formatted Sphinx documentation for a given action definition.

    Args:
        action_name: Name of the action
        action_def: Action definition dictionary

    Returns:
        Sphinx-formatted docstring.
    """
    doc = action_def.get('description', '')

    # append details for all command arguments
    if args := get_args_for_command(action_def):
        args_docs = action_def.get('cmd', {}).get('docs', {})
        for arg in args:
            arg_doc = args_docs.get(arg, 'see protocol manual from manufacturer')
            doc += f'\n:param {arg}: {arg_doc}'

    # append details if a response message is defined for this action
    if vars_dict := get_vars_for_message(action_def):
        msg_docs = action_def.get('msg', {}).get('docs', {})
        doc += '\n:return: {'
        for var in vars_dict:
            var_doc = msg_docs.get(var, 'see protocol manual from manufacturer')
            doc += f'\n   {var}: {var_doc},'
        doc += '\n}'

    return doc
