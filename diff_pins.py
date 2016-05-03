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


import binascii
import subprocess
import re
import sys

import openocd
from bsdl import BsdlJson


def xor(first, second):
    assert len(first) == len(second)
    if first == second:
        return b'0' * len(first)
    else:
        xored = list(binascii.a2b_hex(first))
        tmp = binascii.a2b_hex(second)
        for i in range(0, len(xored)):
            xored[i] ^= tmp[i]
        return binascii.b2a_hex(bytes(xored)).zfill(len(first))

def find_bits(xored):
    bits = []
    for i in range(0, len(xored)):
        nibble = xored[::-1][i] - b'0'[0]
        if nibble != 0:
            for bit in range(0, 4):
                if nibble & (1 << bit):
                    bits.append((i*4) + bit)
    return bits


if __name__ == "__main__":
    bsdl = BsdlJson(sys.argv[1])

    # ocd_process = subprocess.run(["openocd", "-f", "board/digilent_analog_discovery.cfg"])

    with openocd.OpenOcd() as ocd:
        ocd.send("irscan xc6s.tap {}".format(bsdl.sample_opcode))
        original_data = ocd.send("drscan xc6s.tap {} 0".format(bsdl.boundary_length))

    input("Press enter to capture again.")

    with openocd.OpenOcd() as ocd:
        ocd.send("irscan xc6s.tap {}".format(bsdl.sample_opcode))
        new_data = ocd.send("drscan xc6s.tap {} 0".format(bsdl.boundary_length))

    difference = xor(original_data, new_data)
    bits = find_bits(difference)

    for bit in bits:
        print(bsdl.boundary_register[str(bit)])
