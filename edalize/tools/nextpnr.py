# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import os.path

from edalize.tools.edatool import Edatool
from edalize.utils import EdaCommands


class Nextpnr(Edatool):

    description = "A portable FPGA place and route tool"

    TOOL_OPTIONS = {
        "arch": {"type": "str", "desc": "Architecture for nextpnr"},
        "nextpnr_options": {
            "type": "str",
            "desc": "Additional options for nextpnr",
            "list": True,
        },
        "device": {"type": "str", "desc": "FPGA device code"},
        "device_family": {"type": "str", "desc": "FPGA device family code"},
    }

    def setup(self, edam):
        super().setup(edam)
        cst_file = ""
        lpf_file = ""
        pcf_file = ""
        sdc_file = ""
        netlist = ""
        chipdb_file = ""
        placement_constraints = []
        unused_files = []
        for f in self.files:
            file_type = f.get("file_type", "")
            if file_type == "CST":
                if cst_file:
                    raise RuntimeError(
                        "Nextpnr only supports one CST file. Found {} and {}".format(
                            cst_file, f["name"]
                        )
                    )
                cst_file = f["name"]
            if file_type == "LPF":
                if lpf_file:
                    raise RuntimeError(
                        "Nextpnr only supports one LPF file. Found {} and {}".format(
                            pcf_file, f["name"]
                        )
                    )
                lpf_file = f["name"]
            if file_type == "PCF":
                if pcf_file:
                    raise RuntimeError(
                        "Nextpnr only supports one PCF file. Found {} and {}".format(
                            pcf_file, f["name"]
                        )
                    )
                pcf_file = f["name"]
            if file_type == "chipdb":
                if chipdb_file:
                    raise RuntimeError(
                        "Nextpnr only supports one ChipDB (bin/bba) file. Found {} and {}".format(
                            chipdb_file, f["name"]
                        )
                    )
                chipdb_file = f["name"]
            if file_type == "xdc":
                placement_constraints.append(f["name"])
            if file_type == "SDC":
                if sdc_file:
                    raise RuntimeError(
                        "Nextpnr only supports one SDC file. Found {} and {}".format(
                            sdc_file, f["name"]
                        )
                    )
                sdc_file = f["name"]
            elif file_type == "jsonNetlist":
                if netlist:
                    raise RuntimeError(
                        "Nextpnr only supports one netlist. Found {} and {}".format(
                            netlist, f["name"]
                        )
                    )
                netlist = f["name"]
            else:
                unused_files.append(f)

        arch = self._require_tool_option("arch")
        arches = ["xilinx", "ecp5", "gowin", "ice40"]
        if not arch in arches:
            raise RuntimeError("Invalid arch. Allowed options are " + ", ".join(arches))

        self.edam = edam.copy()
        self.edam["files"] = unused_files

        output_files = []

        # Write Makefile
        commands = EdaCommands()

        arch_options = []

        # Specific commands for nextpnr-xilinx
        if arch == "xilinx":
            depends = netlist
            if not chipdb_file:
                raise RuntimeError("Missing required chipdb (bba/bin) file")
            if not placement_constraints:
                raise RuntimeError("Missing required XDC file(s)")
            targets = self.name + ".fasm"
            command = ["nextpnr-" + arch, "--chipdb", chipdb_file]
            xdcs = []
            for x in placement_constraints:
                xdcs += ["--xdc", x]
            command += xdcs
            command += ["--json", depends]
            command += ["--write", self.name + ".routed.json"]
            command += ["--fasm", targets]
            command += ["--log", "nextpnr.log"]
            command += self.tool_options.get("nextpnr_options", [])
            commands.add(command, [targets], [depends])
        else:
            nextpnr_postfix = arch
            if arch == "ecp5":
                targets = self.name + ".config"
                constraints = ["--lpf", lpf_file] if lpf_file else []
                output = ["--textcfg", targets]
            elif arch == "gowin":
                device = self.tool_options.get("device")
                if not device:
                    raise RuntimeError(
                        "Missing required option 'device' for nextpnr-himbaechel"
                    )
                device_family = self.tool_options.get("device_family", "")
                arch_options += ["--device", device]
                arch_options += (
                    ["--vopt", "family={}".format(device_family)]
                    if device_family
                    else []
                )
                targets = self.name + ".routed.json"
                constraints = ["--sdc={}".format(sdc_file)] if sdc_file else []
                constraints += ["--vopt", "cst={}".format(cst_file)] if cst_file else []
                output = ["--write", targets]
                output_files += [
                    {"name": targets, "file_type": "nextpnrRoutedJson"},
                ]
                nextpnr_postfix = "himbaechel"
            else:
                targets = self.name + ".asc"
                constraints = ["--pcf", pcf_file] if pcf_file else []
                output = ["--asc", targets]
                output_files += [
                    {"name": targets, "file_type": "iceboxAscii"},
                ]

            depends = netlist
            command = ["nextpnr-" + nextpnr_postfix, "-l", "next.log"]
            command += arch_options + self.tool_options.get("nextpnr_options", [])
            command += constraints + ["--json", depends] + output

            # CLI target
            commands.add(command, [targets], [depends])

            # GUI target
            commands.add(command + ["--gui"], ["build-gui"], [depends])

        self.edam["files"] += output_files
        commands.set_default_target(targets)
        self.commands = commands
