#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2018 jem@seethis.link
# Licensed under the MIT license (http://opensource.org/licenses/MIT)

from __future__ import absolute_import, division, print_function, unicode_literals

import efm8boot
from efm8boot.bootloader import (EFM8Bootloader, DEBUG_ENABLED)

import easyhid
import sys

if DEBUG_ENABLED:
    from hexdump import hexdump

def find_devices(vid=efm8boot.ids.SILICON_LABS_USB_ID, pid=0x0000, mcu=None, path=None):
    """
    Find all EFM8 HID bootloaders that are connected

    Parameters:
        vid: USB vendor id to match
        pid: USB product id to match
        mcu: microcontroller part name to match
    """
    # Find all Silicon Labs USB IDs
    en = easyhid.Enumeration(vid=vid, pid=pid)

    devices = []

    for hidDevice in en.find(path=path):
        if hidDevice.product_id in efm8boot.ids.EFM8UB_HID_DEVICES:
            boot = efm8boot.EFM8BootloaderHID(hidDevice)

            # if given, check that the mcu part matches
            if mcu and boot.info.name != mcu:
                continue

            devices.append(boot)

    return devices

class EFM8BootloaderHID(EFM8Bootloader):
    HID_IN_SIZE = 4
    HID_OUT_SIZE = 64

    def __init__(self, hidDevice):
        """
        Create the EFM8 bootloader device

        Parameters:
            hidDevice: an easyhid.HIDDevice
        """
        super(EFM8BootloaderHID, self).__init__()
        self._maxPacketSize = self.HID_OUT_SIZE
        self._hidDevice = hidDevice

    @property
    def path(self):
        return self._hidDevice.path

    @property
    def vid(self):
        return self._hidDevice.vendor_id

    @property
    def pid(self):
        return self._hidDevice.product_id

    def connect(self):
        """
        Connect to the USB HID device allowing further communication.
        """
        self._hidDevice.open()
        self._isConnected = True

    def disconnet(self):
        """
        Disconnect from the USB HID device.
        """
        if self._mcuHasBeenReset:
            return
        self._hidDevice.close()
        self._isConnected = False

    def _write(self, data):
        """
        Send data to the HID bootloader.
        """
        data = bytearray(data)
        assert(len(data) <= self._maxPacketSize)

        # Pad to match HID report size
        data += bytearray(self._maxPacketSize - len(data))

        if DEBUG_ENABLED:
            print("Writing to device -> ")
            hexdump(bytes(data))

        # Need to send the data over the control endpoint (EP0), the behaviour
        # of the HID drivers differs between platforms.
        if 'win' in sys.platform:
            # On windows, the windows HID driver will use the EP0 if we
            # send an output report to the interface, and won't allow data to
            # be send using send_feature_report().
            self._hidDevice.write(data)
        else:
            # On Linux the using write()/read() on the HID Device don't use
            # EP0, instead they use the endpoints associated with the HID
            # interface.
            # To write to the HID device on Linux, need to use
            # send_feature_report() as this will be send across EP0.
            self._hidDevice.send_feature_report(data)

    def _read(self, size):
        """
        Read data from the efm8 bootloader.
        """
        assert(size <= self.HID_IN_SIZE)
        if DEBUG_ENABLED:
            print("Read from device -> ")

        # NOTE: Force reads to match HID_IN_SIZE
        # NOTE: See note in `_write()` function above
        if 'win' in sys.platform:
            data = self._hidDevice.read(self.HID_IN_SIZE)
        else:
            data = self._hidDevice.get_feature_report(self.HID_IN_SIZE)

        if DEBUG_ENABLED:
            hexdump(bytes(data))
        return data

    def description(self, short=False):
        """
        Return a string describing the bootloader object.

        Parameters:
            short: if true will use a short form with just the HID and mcu name
        """
        if short:
            return (
                "{:04X}:{:04X} ({}) {}\n"
                .format(
                    self.vid, self.pid, self.path, self.info.name,
                )
            )
        else:
            return (
                "{:04X}:{:04X} {{\n"
                "\tpath = {}\n"
                "\tmcu = {}\n"
                "\tchipID = 0x{:02X}\n"
                "\tflash = {}\n"
                "\tpageSize = {}\n"
                "\tbootloaderStart = 0x{:04X}\n"
                "}}\n"
                .format(
                    self.vid, self.pid, self.path,
                    self.info.name,
                    self.info.chipID,
                    self.info.flashSize,
                    self.info.pageSize,
                    self.info.bootloaderStart,
                )
            )
