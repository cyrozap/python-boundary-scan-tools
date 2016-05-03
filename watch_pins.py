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
import time

import openocd
from bsdl import BsdlJson


def find_bits(data):
    bits = []
    for i in range(0, len(data)):
        byte = data[::-1][i]
        if byte != 0:
            for bit in range(0, 8):
                if byte & (1 << bit):
                    bits.append((i*8) + bit)
    return bits

def draw_chip(pins, pin_map):
    pin_regex = re.compile("([A-Z])([0-9]+)")
    columns = set()
    rows = set()
    mapped_pins = {}
    for signal in pins.keys():
        pin_tuple = pin_regex.match(pin_map[signal][0]).groups()
        row = pin_tuple[0]
        column = int(pin_tuple[1])
        rows.add(row)
        columns.add(column)
        mapped_pins[(row, column)] = pins[signal]

    sys.stdout.write("\x1B[H")
    for column in sorted(list(columns)):
        sys.stdout.write("\t{}".format(column))
    sys.stdout.write("\n".format(column))
    for row in sorted(list(rows)):
        sys.stdout.write("{}\t".format(row))
        for column in sorted(list(columns)):
            pin_data = mapped_pins.get((row, column), {"direction":".", "state":"."})
            if pin_data["direction"] == "IN":
                direction = "I"
            elif pin_data["direction"] == "OUT":
                direction = "O"
            else:
                direction = pin_data["direction"]
            sys.stdout.write("{}*{}\t".format(direction, pin_data["state"]))
        sys.stdout.write("\n")

if __name__ == "__main__":
    bsdl = BsdlJson(sys.argv[1])

    # ocd_process = subprocess.run(["openocd", "-f", "board/digilent_analog_discovery.cfg"])

    with openocd.OpenOcd() as ocd:
        sys.stdout.write("\x1B[2J")
        ocd.send("irscan xc6s.tap {}".format(bsdl.sample_opcode))
        while True:
            boundary_reg = binascii.a2b_hex(ocd.send("drscan xc6s.tap {} 0".format(bsdl.boundary_length)))

            bits = find_bits(boundary_reg)

            pins = {}
            for bit in range(0, bsdl.boundary_length):
                cell = bsdl.boundary_register[str(bit)]
                cell_spec = cell["cell_spec"]
                if cell_spec["port_id"] != "*":
                    entry = {}
                    if cell_spec["function"].upper() == "INPUT":
                        if pins.get(cell_spec["port_id"], {}).get("direction") is not "OUT":
                            entry["direction"] = "IN"
                            entry["state"] = 1 if bit in bits else 0
                            pins[cell_spec["port_id"]] = entry
                    elif cell_spec["function"].upper() == "OUTPUT3":
                        disable_spec = cell["input_or_disable_spec"]
                        control_cell_number = int(disable_spec["control_cell"])
                        disable_value = int(disable_spec["disable_value"])
                        control_cell_state = 1 if control_cell_number in bits else 0
                        if control_cell_state != disable_value:
                            entry["direction"] = "OUT"
                            entry["state"] = 1 if bit in bits else 0
                            pins[cell_spec["port_id"]] = entry

            draw_chip(pins, bsdl.pin_map)
            time.sleep(0.01)
