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


import json


class BsdlJson:
    def __init__(self, bsdljson_file):
        self.json_data = json.load(open(bsdljson_file))
        self.boundary_length = self._get_boundary_length()
        self.sample_opcode = self.get_opcode("SAMPLE")
        self.boundary_register = self._get_boundary_register()
        self.pin_map = self._get_pin_map()

    def _get_boundary_length(self):
        boundary_length_int = 0
        boundary_scan_register_description = self.json_data.get("boundary_scan_register_description")
        if boundary_scan_register_description is not None:
            fixed_boundary_stmts = boundary_scan_register_description.get("fixed_boundary_stmts")
            if fixed_boundary_stmts is not None:
                boundary_length = fixed_boundary_stmts.get("boundary_length")
                if boundary_length is not None:
                    boundary_length_int = int(boundary_length)
        return boundary_length_int

    def get_opcode(self, requested_name):
        opcode = None
        instruction_register_description = self.json_data.get("instruction_register_description")
        if instruction_register_description is not None:
            instruction_opcodes = instruction_register_description.get("instruction_opcodes")
            if instruction_opcodes is not None:
                for instruction_opcode in instruction_opcodes:
                    instruction_name = instruction_opcode.get("instruction_name")
                    if instruction_name.upper() == requested_name.upper():
                        opcode_raw = instruction_opcode.get("opcode_list", [None])[0]
                        if opcode_raw is not None:
                            opcode = int(opcode_raw, 2)
        return opcode

    def _get_boundary_register(self):
        boundary_register = {}
        boundary_scan_register_description = self.json_data.get("boundary_scan_register_description")
        if boundary_scan_register_description is not None:
            fixed_boundary_stmts = boundary_scan_register_description.get("fixed_boundary_stmts")
            if fixed_boundary_stmts is not None:
                boundary_register_list = fixed_boundary_stmts.get("boundary_register")
                if boundary_register_list is not None:
                    for cell in boundary_register_list:
                        cell_number = cell.get("cell_number")
                        if cell_number is not None:
                            cell_info = cell.get("cell_info")
                            if cell_info is not None:
                                boundary_register[cell_number] = cell_info
        return boundary_register

    def _get_pin_map(self):
        pin_map = {}
        pin_map_ast = self.json_data.get("device_package_pin_mappings")[0].get("pin_map")
        if pin_map_ast is not None:
            for entry in pin_map_ast:
                pin_map[entry["port_name"]] = entry["pin_list"]
        return pin_map
