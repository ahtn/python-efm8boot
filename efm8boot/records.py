#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2018 jem@seethis.link
# Licensed under the MIT license (http://opensource.org/licenses/MIT)

from __future__ import absolute_import, division, print_function, unicode_literals

import struct

# Magic values
FRAME_START_BYTE = 0x24
FLASH_KEYS = 0xA5F1

# Command IDs
CMD_IDENTIFY = 0x30
CMD_SETUP    = 0x31
CMD_ERASE    = 0x32
CMD_WRITE    = 0x33
CMD_VERIFY   = 0x34
CMD_LOCK     = 0x35
CMD_RUN_APP  = 0x36

# Command response values
ACK = 0x40
RANGE_ERROR = 0x41
BADID = 0x42
CRC_ERROR = 0x43

ERROR_TO_STRING = {
    ACK : "0x40",
    RANGE_ERROR : "RANGE_ERROR",
    BADID : "BADID",
    CRC_ERROR : "CRC_ERROR",
}

RECORD_HEADER_SIZE = 3

class Record(object):
    """
    Base class for EFM8 bootloader records.

    Format is:
        FRAME_START_BYTE(0x24) : 1 byte
        length                 : 1 byte in range [3,131]
                                 NOTE: Count starts from the command id field
        command id             : 1 byte
        data                   : 2-130 bytes
    """
    def __init__(self, cmd, data):
        self.cmd = cmd
        self.data = data

    def to_bytes(self):
        assert(2 <= len(self.data) <= 130)

        # The length field needs to include everything after it, so need
        # to add +1 for the command ID.
        length = len(self.data) + 1

        return bytearray([
            FRAME_START_BYTE, # first byte frame start byte 0x24
            length,
            self.cmd,
        ]) + bytearray(self.data)

class IdentifyRecord(Record):
    """
    Command used to identify the device.

    Response:
        ACK(0x42) -> device ID match
        BADID(0x42) -> device ID doesn't match
    """
    def __init__(self, id):
        assert(isinstance(id, int) and 0 <= id <= 0xFFFF)
        record_data = struct.pack('>H', id)
        super(IdentifyRecord, self).__init__(CMD_IDENTIFY, record_data)

class SetupRecord(Record):
    """
    Setup command sent to enable flash read and write access.


    Response:
        ACK(0x40)
    """
    def __init__(self, bank=0x00, keys=FLASH_KEYS):
        data = struct.pack('> H B', keys, bank)
        super(SetupRecord, self).__init__(CMD_SETUP, data)

class EraseRecord(Record):
    """
    Erase then write a flash page.

    To erase a page, write an empty data array.  Data to write must not cross a
    page boundary.

    Response:
        ACK(0x40) -> success
        RANGE ERROR(0x41) -> target address range can't be written
    """
    def __init__(self, addr, data):
        address = struct.pack('> H', addr)
        assert(0 <= len(data) <= 128)
        record_data = address + bytearray(data)
        super(EraseRecord, self).__init__(CMD_ERASE, record_data)

class WriteRecord(Record):
    """
    Write a flash page without erasing it first.

    To erase a page, write an empty data array.  Data to write must not cross a
    page boundary.

    Response:
        ACK(0x40) -> success
        RANGE ERROR(0x41) -> target address range can't be written
    """
    def __init__(self, addr, data):
        address = struct.pack('> H', addr)
        assert(1 <= len(data) <= 128)
        record_data = address + bytearray(data)
        super(WriteRecord, self).__init__(CMD_WRITE, record_data)

class VerifyRecord(Record):
    """
    Compute a CRC16 (CCITT-16, XModem) over the flash between the given
    addresses (including endpoints), and compares it with the given CRC value.

    Response:
        ACK(0x40) -> success
        CRC_ERROR(0x41) -> CRC doesn't match
    """
    def __init__(self, addr1, addr2, crc):
        record_data = struct.pack('> H H H', addr1, addr2, crc)
        super(VerifyRecord, self).__init__(CMD_VERIFY, record_data)

class LockRecord(Record):
    """
    Set the bootloader signature and lock bytes.

    Writing a value of 0xff to either sig or lock will leave the value unchanged.

    Parameters:
        sig: bootloader signature byte
        lock: flash lock byte

    Response:
        ACK(0x40) -> success
    """
    def __init__(self, sig=0xff, lock=0xff):
        record_data = struct.pack('>BB', sig, lock)
        super(LockRecord, self).__init__(CMD_LOCK, record_data)

class RunAppRecord(Record):
    """
    Resests the device and starts the application.

    The device will wait 100ms after replying with an ACK before reseting.

    Parameters:
        option: unused

    Response:
        ACK(0x40) -> success
    """
    def __init__(self, option=0x0000):
        record_data = struct.pack('> H', option)
        super(RunAppRecord, self).__init__(CMD_RUN_APP, record_data)
