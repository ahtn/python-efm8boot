#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2018 jem@seethis.link
# Licensed under the MIT license (http://opensource.org/licenses/MIT)

from __future__ import absolute_import, division, print_function, unicode_literals

import efm8boot
import sys
import argparse
import easyhid

EXIT_NO_ERROR = 0
EXIT_ARGUMENTS_ERROR = 1
EXIT_NO_DEVICE_SELECTED = 2

parser = argparse.ArgumentParser(
    description='Flashing script for xusb-boot bootloader'
)

parser.add_argument(
    '-f', dest='flash_hex', action='store',
    type=str,
    default=None,
    help='The hexfile to flash'
),

parser.add_argument(
    '-d', dest='usb_id', action='store',
    default=None,
    metavar="VID:PID",
    help='The VID:PID pair of the device to flash'
)

parser.add_argument(
    '-l', dest='listing',action='store_const',
    const=True, default=False,
    help='If this flag is given, list the available devices'
)

parser.add_argument(
    '-e', dest='erase', action='store_const',
    const=True, default=False,
    help='Erase the flash.'
)

parser.add_argument(
    '-r', dest='reset',  action='store_const',
    const=True, default=False,
    help='Reset the mcu'
)

parser.add_argument(
    '--no-reset', dest='no_reset', action='store_const',
    const=True, default=False,
    help='Don\'t reset after writing flash.'
)

parser.add_argument(
    '-mcu',  action='store',
    default=None,
    help='Check that the bootloader mcu part number matches'
)

parser.add_argument(
    '-p', dest='path',  action='store',
    type=str, default=None,
    help='The device port path. This value can be used to identify a '
    ' device if it does not have a serial number. This value '
    'is not static and may change if the device is reconnected'
)

def parse_vidpid(vidpid):
    # Get the device id which the hex will be flased to.
    try:
        vid, pid = args.id.split(":")
        vid = int(vid, base=16)
        pid = int(pid, base=16)
        if vid > 0xFFFF or pid > 0xFFFF:
            raise Exception
        return (vid, pid)
    except:
        print("bad VID:PID pair: '{}'".format(args.id), file=sys.stderr)
        parser.exit(EXIT_ARGUMENTS_ERROR)

if __name__ == "__main__":
    args = parser.parse_args()

    if not args.flash_hex \
            and not args.erase \
            and not args.reset \
            and not args.listing:
        parser.print_help()
        exit(EXIT_ARGUMENTS_ERROR)

    # open a device by USB id
    if args.usb_id != None:
        vid, pid = parse_vidpid(args.usb_id)
    else:
        vid = efm8boot.ids.SILICON_LABS_USB_ID
        pid = 0x0000 # matches any pid

    # open a device by using its HID path
    devices = efm8boot.find_devices(vid, pid, args.mcu, args.path)

    # List the connected devices
    if args.listing:
        for dev in devices:
            print(dev.description())

    if len(devices) > 1:
        print("Mulitple devices found, exiting...", file=sys.stderr)
        exit(EXIT_NO_DEVICE_SELECTED)
    if len(devices) == 0:
        print("Couldn't open any devices", file=sys.stderr)
        exit(EXIT_NO_DEVICE_SELECTED)

    target = devices[0]

    with target:
        needs_reset = False

        if args.erase:
            target.erase_application_flash()

        if args.flash_hex:
            target.write_flash_hex(args.flash_hex)
            needs_reset = True

        if (args.reset or needs_reset) and not args.no_reset:
            target.reset_mcu()

