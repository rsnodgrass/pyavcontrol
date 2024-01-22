#!/usr/bin/env python3
#
# Running:
#   ./example-async.py --help
#   ./example-async.py --tty /dev/tty.usbserial-A501SGSZ
#   ./example-async.py --tty socket:/remote-server:4999/

import logging
import argparse as arg
import asyncio

import coloredlogs

from pyavcontrol import DeviceClient, DeviceModelLibrary
from pyavcontrol.helper import construct_async_client

LOG = logging.getLogger(__name__)
coloredlogs.install(level='DEBUG')

p = arg.ArgumentParser(description='pyavcontrol client example (asynchronous)')
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


async def main():
    try:
        loop = asyncio.get_event_loop()

        # FIXME: connection!

        config_overrides = {'baudrate': args.baud}
        client = construct_async_client(args.model, args.url, loop, connection_config=config_overrides)

        #       help(client.power)
        await client.send_raw(b'!PING?')
        await client.ping.ping()
        # await client.volume.set(volume=20)
        await client.power.off()

    except Exception as e:
        LOG.error(f'Failed for {args.model}', e)
        return


asyncio.run(main())
