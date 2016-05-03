#!/usr/bin/env python3
#
# Copyright (C) 2016  Forest Crossman <cyrozap@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


import argparse
import binascii
import re
import sys
import time

import openocd
from bsdl import BsdlJson


def get_bit_settings(bit_state_dict, boundary_reg):
    byte_array = list(boundary_reg[::-1])

    for bit in bit_state_dict.keys():
        byte_index = bit // 8
        byte = 1 << (bit % 8)
        if bit_state_dict[bit] == 1:
            byte_array[byte_index] |= byte
        else:
            byte_array[byte_index] &= (~byte & 0xff)

    return binascii.b2a_hex(bytes(byte_array[::-1])).upper()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("bsdl")
    parser.add_argument("pin")
    parser.add_argument("state", type=int, choices=[0, 1])
    args = vars(parser.parse_args())

    bsdl = BsdlJson(args["bsdl"])

    with openocd.OpenOcd() as ocd:
        ocd.send("irscan xc6s.tap {}".format(bsdl.sample_opcode))
        boundary_reg = binascii.a2b_hex(ocd.send("drscan xc6s.tap {} 0".format(bsdl.boundary_length)))

        bit_state_dict = {}
        for bit in range(0, bsdl.boundary_length):
            cell = bsdl.boundary_register[str(bit)]
            cell_spec = cell["cell_spec"]
            if cell_spec["port_id"] == "IO_{}".format(args["pin"]):
                if cell_spec["function"].upper() == "OUTPUT3":
                    disable_spec = cell["input_or_disable_spec"]
                    control_cell_number = int(disable_spec["control_cell"])
                    disable_value = int(disable_spec["disable_value"])
                    enable_value = 0 if disable_value == 1 else 1
                    bit_state_dict[control_cell_number] = enable_value
                    bit_state_dict[bit] = args["state"]

        bit_settings = get_bit_settings(bit_state_dict, boundary_reg).decode("utf-8")

        ocd.send("irscan xc6s.tap {}".format(bsdl.get_opcode("PRELOAD")))
        ocd.send("drscan xc6s.tap {} 0x{}".format(bsdl.boundary_length, bit_settings))

        ocd.send("irscan xc6s.tap {}".format(bsdl.get_opcode("EXTEST")))
        ocd.send("drscan xc6s.tap {} 0x{}".format(bsdl.boundary_length, bit_settings))
