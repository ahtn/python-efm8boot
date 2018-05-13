#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2018 jem@seethis.link
# Licensed under the MIT license (http://opensource.org/licenses/MIT)

from __future__ import absolute_import, division, print_function, unicode_literals

from collections import namedtuple

SILICON_LABS_USB_ID = 0x10C4

EFM8UB1_PREFIX = 0x3200
EFM8UB2_PREFIX = 0x2800
EFM8UB3_PREFIX = 0x3600

EFM8Info = namedtuple(
    'EFM8Info',
    " ".join([
        "chipID",
        "name",
        "flashSize",
        "pinCount",
        "package",
        "pageSize",
        "bootloaderStart",
    ])
)

EFM8UB1_USB_PID = 0xEAC9
EFM8UB1_DEVICES = {
    EFM8UB1_PREFIX | 0x41 : EFM8Info(0x41 , "EFM8UB10F16G_QFN28"  , 16 * 2**10 , 28 , "qfn28"  , 512 , 0x3A00) ,
    EFM8UB1_PREFIX | 0x43 : EFM8Info(0x43 , "EFM8UB10F16G_QFN20"  , 16 * 2**10 , 20 , "qfn20"  , 512 , 0x3A00) ,
    EFM8UB1_PREFIX | 0x45 : EFM8Info(0x45 , "EFM8UB11F16G_QSOP24" , 16 * 2**10 , 24 , "qsop24" , 512 , 0x3A00) ,
    EFM8UB1_PREFIX | 0x49 : EFM8Info(0x49 , "EFM8UB10F8G_QFN20"   , 8 * 2**10  , 20 , "qfn20"  , 512 , 0x1A00) ,
    EFM8UB1_PREFIX | 0x4A : EFM8Info(0x4A , "EFM8UB11F16G_QFN24"  , 16 * 2**10 , 24 , "qfn24"  , 512 , 0x3A00) ,
}

EFM8UB2_USB_PID = 0xEACA
EFM8UB2_DEVICES = {
    EFM8UB2_PREFIX | 0x60 : EFM8Info(0x60 , "EFM8UB20F64G_QFP48" , 64 * 2**10 , 48 , "qfp48" , 512 , 0xF600) ,
    EFM8UB2_PREFIX | 0x61 : EFM8Info(0x61 , "EFM8UB20F64G_QFP32" , 64 * 2**10 , 32 , "qfp32" , 512 , 0xF600) ,
    EFM8UB2_PREFIX | 0x62 : EFM8Info(0x62 , "EFM8UB20F64G_QFN32" , 64 * 2**10 , 32 , "qfn32" , 512 , 0xF600) ,
    EFM8UB2_PREFIX | 0x63 : EFM8Info(0x63 , "EFM8UB20F32G_QFP48" , 32 * 2**10 , 48 , "qfp48" , 512 , 0x7A00) ,
    EFM8UB2_PREFIX | 0x64 : EFM8Info(0x64 , "EFM8UB20F32G_QFP32" , 32 * 2**10 , 32 , "qfp32" , 512 , 0x7A00) ,
    EFM8UB2_PREFIX | 0x65 : EFM8Info(0x65 , "EFM8UB20F32G_QFN32" , 32 * 2**10 , 32 , "qfn32" , 512 , 0x7A00) ,
}

EFM8UB3_USB_PID = 0xEACB
EFM8UB3_DEVICES = {
    EFM8UB3_PREFIX | 0x00 : EFM8Info(0x00 , "EFM8UB30F40G_QFN20"  , 40 * 2**10 , 20 , "qfn20"  , 512 , 0x9A00) ,
    EFM8UB3_PREFIX | 0x01 : EFM8Info(0x01 , "EFM8UB31F40G_QFN24"  , 40 * 2**10 , 24 , "qfn24"  , 512 , 0x9A00) ,
    EFM8UB3_PREFIX | 0x02 : EFM8Info(0x02 , "EFM8UB31F40G_QSOP24" , 40 * 2**10 , 24 , "qsop24" , 512 , 0x9A00) ,
}

EFM8UB_HID_DEVICES = {
    EFM8UB1_USB_PID : EFM8UB1_DEVICES,
    EFM8UB2_USB_PID : EFM8UB2_DEVICES,
    EFM8UB3_USB_PID : EFM8UB3_DEVICES,
}
