#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2018 jem@seethis.link
# Licensed under the MIT license (http://opensource.org/licenses/MIT)

from __future__ import absolute_import, division, print_function, unicode_literals

import efm8boot
from efm8boot.bootloader import (EFM8Bootloader, DEBUG_ENABLED)

if DEBUG_ENABLED:
    from hexdump import hexdump


HID_IN_SIZE = 4
HID_OUT_SIZE = 64

class EFM8BootloaderSMBus(EFM8Bootloader):
    """ TODO: Support SMBus bootloader """

    def __init__(self, hidDevice):
        """
        Create the EFM8 bootloader device

        Parameters:
            hidDevice: an easyhid.HIDDevice
        """
        super().__init__(hidDevice)
        self._maxPacketSize = HID_OUT_SIZE

    def connect(self):
        """
        Connect to the USB HID device allowing further communication.
        """
        self._isConnected = True

    def disconnet(self):
        """
        Disconnect from the USB HID device.
        """
        self._isConnected = False

    def _write(self, data):
        """
        Send data to the HID bootloader.
        """
        data = bytes(data)
        assert(len(data) <= self._maxPacketSize)

        if DEBUG_ENABLED:
            print("Writing to device -> ")
            hexdump(bytes(data))

    def _read(self, size):
        """
        Read data from the efm8 bootloader.
        """
        assert(size <= HID_IN_SIZE)
        if DEBUG_ENABLED:
            print("Read from device -> ")

        data = None

        if DEBUG_ENABLED:
            hexdump(bytes(data))
        return data
