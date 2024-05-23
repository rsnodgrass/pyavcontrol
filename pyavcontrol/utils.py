import logging
import re

LOG = logging.getLogger(__name__)

NAMED_REGEX_PATTERN = re.compile(r'\(\?P<(?P<name>.+)>(?P<regex>.+)\)')
FSTRING_ARG_PATTERN = re.compile(r'{(?P<arg_name>.+)}')


def extract_named_regex(text: str) -> dict:
    """
    Parse out named regex patterns from text into a dictionary of
    names and associated regex.
    """
    named_regex = {}
    for m in NAMED_REGEX_PATTERN.finditer(text):
        named_regex[m.group(1)] = m.group(2)
    return named_regex


def missing_keys_in_dict(required_keys: list[str], d: dict) -> list[str]:
    """
    Checks that the provided dictionary contains all the required keys,
    and if not, return a list of the missing keys.
    """
    missing_keys = []
    for key in required_keys:
        if key not in d:
            missing_keys += key
    return missing_keys


def substitute_fstring_vars(fstring: str, vars: dict) -> str:
    # see also https://stackoverflow.com/questions/42497625/how-to-postpone-defer-the-evaluation-of-f-strings
    return fstring.format(**vars)


def get_fstring_vars(text: str) -> list[str]:
    """
    Parse out all the F-string style arguments from the given string with the
    name and the complete formatting as value.
    """
    vars = []

    # extract args from the regexp pattern of parameters
    for m in FSTRING_ARG_PATTERN.finditer(text):
        var = m.group(1)
        # remove any special format strings in the var to just get the name
        var = var.split(':')[0]
        vars.append(var)
    return vars


def camel_case(text: str) -> str:
    """
    Convert string into a CamelCase format without any spaces or special characters
    """
    return re.sub('[^0-9a-zA-Z]+', '', re.sub('[-_.]+', ' ', text).title())


def get_subkey(dictionary: dict, top_key: str, key: str, log_missing=True):
    """Load a subkey from a nested dictionary and log if missing"""
    d = dictionary.get(top_key)
    if not d:
        if log_missing:
            LOG.warning(
                f"Missing top level key '{top_key}' for subkey '{key}'; returning None"
            )
        return None

    value = dictionary.get(key)
    if value is None and log_missing:
        LOG.warning(f"Missing subkey '{key}' under key '{top_key}'; returning None")
    return value


def get_vars_for_message(action_def: dict) -> dict:
    """
    Parse out all variables returned in the msg response for this action.
    :return: list of variables for the message
    """
    if msg := action_def.get('msg'):
        if regex := msg.get('regex'):
            named_regex = extract_named_regex(regex)
            return named_regex

    return {}


def get_args_for_command(action_def: dict) -> list[str]:
    """
    Parse the command definition into an array of arguments for the action, with a dictionary
    describing additional type information about each argument.
    :return: list of arguments for a given command
    """
    if cmd := action_def.get('cmd'):
        #        if regex := cmd.get('regex'):
        #            named_regex = extract_named_regex(regex)
        #            LOG.info(f'Command regex found BUT IGNORING! {named_regex}')

        fstring = cmd.get('fstring')
        if args := get_fstring_vars(fstring):
            # FIXME: embed all the cmd_patterns into this
            return args

    return []


def generate_docs_for_action(action_name: str, action_def: dict):
    """Return formatted Sphinx documentation for a given action definition"""
    doc = action_def.get('description', '')

    # append details for all command arguments
    if args := get_args_for_command(action_def):
        args_docs = action_def.get('cmd', {}).get('docs', {})
        for arg in args:
            arg_doc = args_docs.get(arg, 'see protocol manual from manufacturer')
            doc += f'\n:param {arg}: {arg_doc}'

    # append details if a response message is defined for this action
    if v := get_vars_for_message(action_def):
        msg_docs = action_def.get('msg', {}).get('docs', {})
        doc += '\n:return: {'
        for var in v:
            var_doc = msg_docs.get(var, 'see protocol manual from manufacturer')
            doc += f'\n   {var}: {var_doc},'
        doc += '\n}'

    # FIXME: may need type info from the overall api variables section
    return doc
