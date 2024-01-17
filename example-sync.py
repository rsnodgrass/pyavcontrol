#!/usr/bin/env python3
#
# Running:
#   ./example-async.py --help
#   ./example.py --tty /dev/tty.usbserial-A501SGSZ

import logging
import argparse as arg

import coloredlogs

from pyavcontrol import DeviceClient, DeviceModelLibrary

LOG = logging.getLogger(__name__)
coloredlogs.install(level='DEBUG')

p = arg.ArgumentParser(description='pyavcontrol client example (synchronous)')
p.add_argument(
    '--url',
    help='pyserial supported url for communication (e.g. /dev/tty.usbserial-A501SGSZ or socket://host:4999/)',
    default='socket://localhost:4999/',
)
p.add_argument(
    '--model', default='mcintosh_mx160', help='device model (e.g. mcintosh_mx160)'
)
p.add_argument(
    '--baud',
    type=int,
    default=115200,
    help='baud rate if local tty used (default=115200)',
)
p.add_argument('-d', '--debug', action='store_true', help='verbose logging')
args = p.parse_args()

if args.debug:
    logging.getLogger().setLevel(level=logging.DEBUG)


def main():
    model_def = DeviceModelLibrary.create().load_model(args.model)
    client = DeviceClient.create(
        model_def, args.url, connection_config_overrides={'baudrate': args.baud}
    )

    client.send_raw(b'!PING?')
    print(client.ping.ping())
    client.power.off()
    client.ping.ping()
    client.ping.ping()


main()
