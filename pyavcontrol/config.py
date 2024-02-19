from dataclasses import dataclass

@dataclass(frozen=True)
class _ConfigKeys:
    api = 'api'
    baudrate = 'baudrate'
    clear_before_new_commands = 'clear_before_new_commands'
    command_eol = 'command_eol'
    command_separator = 'command_separator'
    description = 'description'
    encoding = 'encoding'
    id = 'id'
    message_eol = 'message_eol'
    min_time_between_commands = 'min_time_between_commands'
    model = 'model'
    name = 'name'
    protocol = 'protocol'
    serial_config = 'serial_config'
    timeout = 'timeout'
    urls = 'urls'


CONFIG = _ConfigKeys()

# FIXME: see schema!

# FIXME: other explorations below
# https://dev.to/eblocha/using-dataclasses-for-configuration-in-python-4o53
#
# raw_config = {...}
# config = Order.from_dict(raw_config)
# config.customer.first_name



# FIXME: if we want completely dynamic config we can use below
# https://alexandra-zaharia.github.io/posts/python-configuration-and-dataclasses/
# config = DynamicConfig({'host': 'example.com', 'port': 80, 'timeout': 0.5})
# print(f'host: {config.host}, port: {config.port}, timeout: {config.timeout}')
class DynamicConfig:
    def __init__(self, conf):
        if not isinstance(conf, dict):
            raise TypeError(f'dict expected, found {type(conf).__name__}')

        self._raw = conf
        for key, value in self._raw.items():
            setattr(self, key, value)
