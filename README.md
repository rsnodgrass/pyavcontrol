# Python Control of A/V Equipment (RS232 / IP)

![beta_badge](https://img.shields.io/badge/maturity-Beta-yellow.png)
[![PyPi](https://img.shields.io/pypi/v/pyavcontrol.svg)](https://pypi.python.org/pypi/pyavcontrol)
[![MIT license](http://img.shields.io/badge/license-MIT-brightgreen.svg)](http://opensource.org/licenses/MIT)
[![Build Status](https://github.com/rsnodgrass/pyavcontrol/actions/workflows/ci.yml/badge.svg)](https://github.com/rsnodgrass/pyavcontrol/actions/workflows/ci.yml)

[![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=WREP29UDAMB6G)
[![Buy Me A Coffee](https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg)](https://buymeacoffee.com/DYks67r)

Library created to control a wide variety of A/V equipment which expose text-based control
protocols over RS232, USB serial connections, and/or remote IP sockets.

### Background

This `pyavcontrol` library evolved from learnings during implementation a half dozen
custom client libraries for controlling specific equipment such as  [pyxantech](https://github.com/rsnodgrass/pyxantech) and pyanthem-serial, which
were used to expose integrations for [Home Assistant](https://home-assistant.io).

From those learnings, it was observed that the control protocols were often fairly similar and typically
simple pattern matching could be used for converting the interfaces into more modern dictionary based APIs.
This couples with dynamic Python class creation based on YAML protocol definition files for the protocols enables
quickly spinning up new interfaces for specific devices even by anyone who has the ability to read technical
documentation on the protocols (and not just those who are software developers).

Two additional goals:

1. allow clients in other programming languages to share the same YAML protocol definitions to provide similar dynamic APIs that support a wide variety of devices quickly.
2. Create a basic IP-based RS232 emulator which allows spinning up a basic emulator for each supported
device model based purely on the YAML definition and unit tests against those definitions. This emulator can be used by client libraries in any language for testing. See [avemu]() for more details.


## Support

Visit the [community support discussion thread](https://community.home-assistant.io/t/mcintosh/) for issues with this library.

## Emulator

Of particular interest, is the included device emulator which takes a properly defined
device's protocol and starts a server that will respond to all commands as if the
a physical device was connected. This is exceptionally useful for testing AND can be
used by clients developed in other languages as well.

Example starting the McIntosh MX160 emulator:

```
./emulator.py --model mx160 -d
```

## Supported Equipment

See [SUPPORTED.md](SUPPORTED.md) for the complete list of supported equipment.

## Background

One annoying thing when developing `pyxantech` was that none of the devices
ever had a protocol definition in a machine-readable format. Manufacturers
would provide a PDF or XLS document (if anything at all) that listed
the various commands that could be sent via RS232. However, there was no
consistency for what were generally very similar callable actions when
controlling preamps/receivers/etc.

During the development of `pyxantech` it became clear that other manufacturers
had copied the protocol developed by Xantech, with each
manufacturer just making a very small change in the prefixes or suffixes.
From this, a very primitive mechanism was built. YAML was chosen
to be a machine-readable format that was also easily read/updated by humans
who may have limited programming skills.

This makes it easier and quicker to
add support for new devices without having to build an entirely new library each
time (with varying semantics and degrees of testing/clarity/documentation).
Additionally, these definitions make it possible to create similar libraries in
a variety of languages, all sharing the same protocol definitions.

The evolution found in this `pyavcontrol` library takes these ideas further by
having a much more cohesive definition of protocols. Additional ideas were
discovered in [onkyo-eiscp](https://github.com/miracle2k/onkyo-eiscp) around
providing a simple CLI to use the library and grouping commands together
logically. These ideas combined with the argument definitions and pattern
matching from `pyxantech` moved these ideas closer to reality.

If you are trying to implement your own interface to McIntosh in other
languages besides Python, you should consider using the YAML series and
protocol files from this repository as a basis for the interface you provide.
The protocol and series definitions will likely be split out into separate
definition-only package(s) in the future.

## Using pyavcontrol

### Asynchronous & Synchronous APIs

This library provides both an `asyncio` based and synchronous implementations.
By default, the synchronous implementation is returned when instantiating
new objects unless an `event_loop` is passed in when creating
DeviceModelLibrary or DeviceClient objects.

Async example:

```python
    loop = asyncio.get_event_loop()

library = DeviceModelLibrary.create(event_loop=loop)
model_definition = library.load_model("mcintosh_mx160")

client = DeviceClient.create(
    model_definition,
    url,
    connection_config_overrides=config,
    event_loop=loop
)

await client.power.on()
await client.volume.set(50)
```

### Connection URL

This interface uses URLs for specifying the communication transport
to use, as defined in [pyserial](https://pyserial.readthedocs.io/en/latest/url_handlers.html), to allow a wide variety of underlying mechanisms.

For example:

| URL                      | Notes                                                                                               |
| ------------------------ | --------------------------------------------------------------------------------------------------- |
| `/dev/ttyUSB0`           | directly attached serial device (Linux)                                                             |
| `COM3`                   | directly attached serial device (Windows)                                                           |
| `socket://<host>:<port>` | remote host that exposes RS232 over TCP ``*`` |
| `socket://mx160.local:84` | direct connection to MX160's port 84 interface |

* See [IP2SL](https://github.com/rsnodgrass/virtual-ip2sl) for example RS2332 over TCP.

See [pyserial](https://pyserial.readthedocs.io/en/latest/url_handlers.html) for additional formats supported.

## Future Ideas

- Add programmatic override/enhancements to the base protocol where pure
  YAML configuration would not work fully. Of course, these overrides would have
  to be implemented in each language, but that surface area should be much smaller.

## See Also

- [avemu - A/V Equipment Emulator](https://github.com/rsnodgrass/avemu) (very useful for testing client libraries)
- [Earlier McIntosh control in Home Assistant](https://community.home-assistant.io/t/need-help-using-rs232-to-control-a-receiver/95210/8)
- https://drivers.control4.com/solr/drivers/browse?q=mcintosh
