#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2018 jem@seethis.link
# Licensed under the MIT license (http://opensource.org/licenses/MIT)

from __future__ import absolute_import, division, print_function, unicode_literals

from efm8boot.records import (
    IdentifyRecord, RunAppRecord, SetupRecord, EraseRecord, WriteRecord,
    LockRecord, VerifyRecord
)
import efm8boot.ids

DEBUG_ENABLED = 1

if DEBUG_ENABLED:
    from hexdump import hexdump

class EFM8BootloaderError(Exception):
    def __init__(self, code):
        super().__init__("EFM8 bootloader error: 0x{:02X}".format(code))
        self.code = code

class EFM8BootloaderHID(object):
    def __init__(self, hid_device):
        self._hid_dev = hid_device
        self._mcu_has_been_reset = False

        with self:
            self.device_info = self.get_device_info()

    def connect(self):
        self._hid_dev.open()

    def disconnet(self):
        if self._mcu_has_been_reset:
            return
        self._hid_dev.close()

    def __enter__(self):
        self.connect()

    def __exit__(self, err_type, err_value, traceback):
        self.disconnet()

    def _write(self, data):
        data = bytes(data)

        if DEBUG_ENABLED:
            print("Writing to device -> ")
            hexdump(bytes(data))
        self._hid_dev.send_feature_report(data)

    def _write_record(self, record, raise_error=True):
        self._write(record.to_bytes())
        resp = self._read(1)[0]
        if raise_error:
            if resp != efm8boot.records.ACK:
                raise EFM8BootloaderError(resp)
        else:
            return resp

    def _read(self, size):
        if DEBUG_ENABLED:
            print("Read from device -> ")
        data = self._hid_dev.get_feature_report(size)

        if DEBUG_ENABLED:
            hexdump(bytes(data))
        return data

    def identify(self, id):
        """
        Checks if the bootloader device against the given id.

        Returns:
            True if the device matches the given id
        """
        resp = self._write_record(IdentifyRecord(id), raise_error=False)
        return resp != efm8boot.records.BADID

    def get_device_info(self):
        """
        Attempt to identify the connected device, by repeated calling the
        identify command until a match is found.

        Returns:
            A named tuple with device information, or None if an unknown device
            was found
        """
        device_family = efm8boot.ids.EFM8UB_HID_DEVICES[self._hid_dev.product_id]
        for id in device_family:
            if self.identify(id):
                return device_family[id]
        return None

    def enable_modifications(self):
        """
        Enable flash modifications
        """
        self._write_record(SetupRecord())

    def erase_page(self, addr):
        assert(addr < self.device_info.bootloader_start)
        self._write_record(EraseRecord(addr, []))

    def write_page(self, addr, data, erase=True):
        assert(addr < self.device_info.bootloader_start)
        page_size = self.device_info.page_size
        assert((addr%page_size) + len(data) <= page_size)
        if erase:
            # Erase before write
            self._write_record(EraseRecord(addr, data))
        else:
            # Don't erase before write
            self._write_record(WriteRecord(addr, data))

    def disable_bootloader(self):
        self._write_record(LockRecord(sig=0x00))

    def lock(self, lock_byte):
        self._write_record(LockRecord(lock=lock_byte))

    def verify(self, start, end, crc):
        assert(start <= end)
        self._write_record(VerifyRecord(start, end, crc))

    def reset_mcu(self):
        """
        Resets the device and runs the app
        """
        self._write_record(RunAppRecord())
