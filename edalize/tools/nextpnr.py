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
    }

    def configure(self, edam):
        super().configure(edam)
        cst_file = ""
        lpf_file = ""
        pcf_file = ""
        netlist = ""
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

        self.edam = edam.copy()
        self.edam["files"] = unused_files
        of = [
            {"name": self.name + ".asc", "file_type": "iceboxAscii"},
        ]
        self.edam["files"] += of

        # Write Makefile
        commands = EdaCommands()

        arch = self.tool_options["arch"]
        arch_options = []
        if arch == "ecp5":
            targets = self.name + ".config"
            constraints = ["--lpf", lpf_file] if lpf_file else []
            output = ["--textcfg", targets]
        elif arch == "gowin":
            device = self.tool_options.get("device")
            if not device:
                raise RuntimeError("Missing required option 'device' for nextpnr-gowin")
            arch_options += ["--device", device]
            targets = self.name + ".pack"
            constraints = ["--cst", cst_file] if cst_file else []
            output = ["--write", targets]
        else:
            targets = self.name + ".asc"
            constraints = ["--pcf", pcf_file] if pcf_file else []
            output = ["--asc", targets]

        depends = netlist
        command = ["nextpnr-" + arch, "-l", "next.log"]
        command += arch_options + self.tool_options.get("nextpnr_options", [])
        command += constraints + ["--json", depends] + output

        # CLI target
        commands.add(command, [targets], [depends])

        # GUI target
        commands.add(command + ["--gui"], ["build-gui"], [depends])
        self.commands = commands.commands
