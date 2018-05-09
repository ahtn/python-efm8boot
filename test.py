#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2018 jem@seethis.link
# Licensed under the MIT license (http://opensource.org/licenses/MIT)

from __future__ import absolute_import, division, print_function, unicode_literals

import efm8boot
import easyhid

# Find all Silicon Labs USB IDs
en = easyhid.Enumeration(vid=efm8boot.ids.SILICON_LABS_USB_ID)

for dev in en.find():
    if dev.product_id in efm8boot.ids.EFM8UB_HID_DEVICES:
        boot = efm8boot.EFM8BootloaderHID(dev)
        print(boot.device_info)

        with boot:
            boot.enable_modifications()
            boot.write_page(0x200, [1, 2, 3, 4, 5, 6, 7, 8, 9], erase=False)
            boot.reset_mcu()
