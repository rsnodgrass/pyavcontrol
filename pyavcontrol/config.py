from dataclasses import dataclass

@dataclass(frozen=True)
class _Config:
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


CONFIG = _Config()

# FIXME: other explorations below
# https://dev.to/eblocha/using-dataclasses-for-configuration-in-python-4o53
#
# raw_config = {...}
# config = Order.from_dict(raw_config)
# config.customer.first_name


@dataclass
class ManufacturerInfo:
    name: str
    model: str

    def __init__(self, conf):
        self.name = conf[CONFIG.name]
        self.model = conf[CONFIG.model]

    def __post_init__(self):
        if not self.name:
            raise ValueError('name must be defined')
        if not self.model:
            raise ValueError('model must be defined')


@dataclass
class ModelDefinition:
    id: str
    description: str
    urls: list[str]

    manufacturer: ManufacturerInfo

    def __init__(self, conf: dict):
        self.id = conf[CONFIG.id]
        self.description = conf[CONFIG.description]
        self.urls = conf[CONFIG.urls]

        self.manufacturer = ManufacturerInfo(conf)

    def __post_init__(self):
        if not self.id:
            raise ValueError('id must be defined')


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
