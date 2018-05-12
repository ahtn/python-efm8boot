#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2018 jem@seethis.link
# Licensed under the MIT license (http://opensource.org/licenses/MIT)

from __future__ import absolute_import, division, print_function, unicode_literals

from efm8boot.records import (
    Record, IdentifyRecord, RunAppRecord, SetupRecord, EraseRecord,
    WriteRecord, LockRecord, VerifyRecord, RECORD_HEADER_SIZE, ERROR_TO_STRING
)
import efm8boot.ids

import intelhex
import crcmod
import math

DEBUG_ENABLED = 0

FRAME_SIZE = 128

class EFM8BootloaderError(Exception):
    pass

class EFM8BootloaderProtocolError(EFM8BootloaderError):
    """
    EFM8 bootloader protocol error
    """
    def __init__(self, code):
        super().__init__(
            "EFM8 bootloader error: {}".format(ERROR_TO_STRING[code])
        )
        self.code = code

class EFM8BootloaderHexError(EFM8BootloaderError):
    """
    Error used when a hex file is incompatible with the bootloader.
    """
    pass

class EFM8BootloaderSMBus(object):
    """ TODO: Support SMBus bootloader """
    pass


class EFM8Bootloader(object):
    """
    EFM8 bootloader base class
    """

    def __init__(self):
        self._mcuHasBeenReset = False
        self._hasLoadedInfo = False
        self._isConnected = False
        self._isWritingEnabled = False

        self.compute_crc = crcmod.predefined.mkCrcFun('xmodem')

    @property
    def info(self):
        if self._hasLoadedInfo:
            return self._info

        if self._isConnected:
            # Don't need to connect if already connected
            return self._get_device_info()
        else:
            # Connect and disconnect after getting the device info
            with self:
                return self._get_device_info()

    def __enter__(self):
        self.connect()

    def __exit__(self, err_type, err_value, traceback):
        self.disconnet()

    def _write_record(self, record, raiseError=True):
        """
        Send data to the efm8 bootloader using the efm8 bootloader record format.
        """

        recordData = record.to_bytes()

        # Can only send 64 bytes at a time, so packetize the data if necessary
        for offset in range(0, len(recordData), self._maxPacketSize):
            self._write(recordData[offset : offset+self._maxPacketSize])

        # Read the response and check for errors
        resp = self._read(1)[0]

        if raiseError:
            if resp != efm8boot.records.ACK:
                raise EFM8BootloaderProtocolError(resp)
        else:
            return resp

    def identify(self, id):
        """
        Checks if the bootloader device against the given id.

        Parameters:
            id: the ID to match against.

        Returns:
            True if the device matches the given id
        """
        resp = self._write_record(IdentifyRecord(id), raiseError=False)
        return resp != efm8boot.records.BADID

    def _get_device_info(self):
        """
        Attempt to identify the connected device, by repeated calling the
        identify command until a match is found.

        Returns:
            A named tuple with device information, or None if an unknown device
            was found
        """
        deviceFamily = efm8boot.ids.EFM8UB_HID_DEVICES[self._hidDevice.product_id]

        for id in deviceFamily:
            if self.identify(id):
                self._info = deviceFamily[id]
                self._hasLoadedInfo = True
                return self._info

        raise EFM8BootloaderError("Could not identify EFM8 HID device")

    def get_version(self):
        """
        Get the bootloader version.
        """
        # When the bootloader receives an unknown cmd ID, it will return the
        # version of the bootloader.
        return self._write_record(Record(cmd=0x00, data=[0x00, 0x00]), raiseError=False)

    def enable_modifications(self):
        """
        Enable flash modifications while the bootloader is running
        """
        if self._isWritingEnabled:
            return

        self._write_record(SetupRecord())
        self._isWritingEnabled = True

    def disable_modifications(self):
        """
        Disable flash modifications while the bootloader is running
        """
        self._write_record(SetupRecord(keys=0x0000))
        self._isWritingEnabled = False

    def erase_page(self, addr):
        """
        Erase the given flash page.

        Note:
            Must call enable_modifications() before this function will work.

        Parameters:
            addr: a pointer anywhere inside the page
        """
        assert(addr < self.info.bootloaderStart)
        self._write_record(EraseRecord(addr, []))

    def erase_application_flash(self):
        """
        Erase the entire application flash
        """
        self._auto_modify_enable()
        for pageAddr in range(0x0000, self.info.bootloaderStart, self.info.pageSize):
            self.erase_page(pageAddr)
        self._auto_modify_disable()

    def write_packet(self, addr, data, erase=True):
        """
        Write a packet to the efm8 bootloader flash.

        Note:
            Must call enable_modifications() before this function will work.

        Parameters:
            addr: the address to write
            data: the data to write to the page. Length must be less than 128 bytes
            erase: set to true to erase the flash page before writing
        """
        assert(addr < self.info.bootloaderStart)
        assert(len(data) <= FRAME_SIZE)

        if erase:
            # Erase before write
            self._write_record(EraseRecord(addr, data))
        else:
            # Don't erase before write
            self._write_record(WriteRecord(addr, data))

    def write_page(self, pageAddr, data, erase=True):
        """
        Write a page to the efm8 bootloader flash.

        Note:
            Must call enable_modifications() before this function will work.

        Parameters:
            pageAddr: the address of the flash page
            data: the data to write to the page.
            erase: set to true to erase the flash page before writing
        """
        assert(pageAddr < self.info.bootloaderStart)
        assert(pageAddr % self.info.pageSize == 0)
        assert(len(data) == self.info.pageSize)

        for offset in range(0, self.info.pageSize, FRAME_SIZE):
            # only erase if this is the first packet in the page to write
            shouldErase = (offset == 0) and erase

            self.write_packet(
                pageAddr + offset,
                data[offset : offset + FRAME_SIZE],
                shouldErase
            )

    def _packetizeHex(self, ihex, pageSize):
        """
        Return all the pages in an intelhex file that contain data.

        Parameters:
            ihex: an intelhex.IntelHex file object
            pageSize: the size of the pages

        Returns:
            An array of page tuples in the form `(pageAddr, pageData)`.
        """
        pages = []
        nextPage = 0x0000

        # iterate through all the bytes in the hex file
        for curAddr in ihex.addresses():
            if curAddr < nextPage:
                continue

            pageStart = math.floor(curAddr / self.info.pageSize) * self.info.pageSize
            newPage = ihex.tobinstr(start=pageStart, size=self.info.pageSize)
            pages.append((pageStart, newPage))

            nextPage = pageStart + self.info.pageSize

        return pages

    def write_flash_hex(self, hexFile, hexFormat='hex'):
        """
        Write a hex file to the bootloader.

        Parameters:
            hexFile: file name or file-like object
            hexFormat: file format ('hex' or 'bin')
        """
        ihex = intelhex.IntelHex()
        ihex.fromfile(hexFile, hexFormat)

        # check that the hex file fits into the application section
        if ihex.maxaddr() >= self.info.bootloaderStart:
            raise EFM8BootloaderHexError(
                "Hex file too large. Available space for application is {} "
                "bytes, but got {} bytes.".format(
                    self.info.bootloaderStart,
                    ihex.maxaddr(),
                )
            )

        # get a list of flash pages from the hex file
        pages = self._packetizeHex(ihex, self.info.pageSize)

        if len(pages) == 0:
            return

        firstPageAddr = pages[0][0]
        firstPageData = pages[0][1]

        # Enable writing to flash
        self._auto_modify_enable()

        # The bootloader checks the flash byte at 0x0000 to determine if the
        # flash is empty and will run the bootloader at start up if it is.
        #
        # To help improve reliability erase this page first and write it last.
        # This way, if the bootloader is interrupted before it can write this
        # page, when the device is reset, it will still enter the bootloader.
        if firstPageAddr == 0x0000:
            # Erase the page at start of flash
            self.erase_page(firstPageAddr)
        else:
            # If the hex file doesn't write to 0x0000, then write the page now
            self.write_page(firstPageAddr, firstPageData)

        # Write all the other pages
        for (pageAddr, pageData) in pages[1:]:
            self.write_page(pageAddr, pageData)

        # Finally, write the page at start of flash
        if firstPageAddr == 0x0000:
            self.write_page(firstPageAddr, firstPageData, erase=False)

        for (segStart, segEnd) in ihex.segments():
            crc = self.compute_crc(ihex.tobinstr(segStart, segEnd))
            self.verify(segStart, segEnd, crc)

        # Disable further flash modifications
        self._auto_modify_disable()

    def disable_bootloader(self):
        """
        Disable the bootloader by clearing the bootloader signature byte.

        When the bootloader is enabled, it is the first piece of code that
        runs on a mcu reset. When the bootloader is
        """
        self._write_record(LockRecord(sig=0x00))

    def _auto_modify_enable(self):
        """
        Same as enable_modifications, except will restore modify state when
        `_auto_modify_disable()` is callled
        """
        # If flash modifications are not enabled, auto disable them
        self._autoDisable = not self._isWritingEnabled
        self.enable_modifications()

    def _auto_modify_disable(self):
        """
        Same as disable_modifications, except will restore modify state when
        used with `_auto_modify_enable()`
        """
        if self._autoDisable:
            self.disable_modifications()

    def lock(self, lock_byte):
        """
        Set the efm8 lock byte.
        """

        self._write_record(LockRecord(lock=lock_byte))

    def verify(self, start, end, crc):
        """
        Compute a CRC16 (CCITT-16, XModem) on the given flash region, and
        compare it against the given `crc` value.

        Note:
            Must call enable_modifications() before this function will work.

        Parameters:
            start: start address of the flash region
            end: end address of the flash region (inclusive)
            crc: the value to compare the CRC against

        Raises:
            EFM8BootloaderProtocolError: if the crc does not match
        """
        assert(start <= end)
        self._write_record(VerifyRecord(start, end, crc))

    def reset_mcu(self):
        """
        Resets the device and runs the application code.
        """
        self._write_record(RunAppRecord())
