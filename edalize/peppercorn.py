# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import os.path
import re

from edalize.edatool import Edatool
from edalize.nextpnr import Nextpnr
from edalize.utils import EdaCommands
from edalize.yosys import Yosys


class Peppercorn(Edatool):

    argtypes = ["vlogdefine", "vlogparam"]

    @classmethod
    def get_doc(cls, api_ver):
        if api_ver == 0:
            options = {
                "members": [
                    {
                        "name": "device",
                        "type": "String",
                        "desc": "Required device option for nextpnr (e.g. CCGM1A1)",
                    }
                ],
                "lists": [
                    {
                        "name": "gmpack_options",
                        "type": "String",
                        "desc": "Additional options for gmpack",
                    },
                ],
            }

            Edatool._extend_options(options, Yosys)
            Edatool._extend_options(options, Nextpnr)

            return {
                "description": "Open source toolchain for CologneChip GateMate.",
                "members": options["members"],
                "lists": options["lists"],
            }

    def configure_main(self):
        # Pass peppercorn options to yosys and nextpnr
        self.edam["tool_options"] = {
            "yosys": {
                "arch": "gatemate",
                "output_format": "json",
                "yosys_synth_options": self.tool_options.get("yosys_synth_options", [
                    "-luttree", "-nomx8"]),
                "yosys_as_subtool": True,
                "yosys_template": self.tool_options.get("yosys_template"),
            },
            "nextpnr": {
                "device": self.tool_options.get("device"),
                "nextpnr_options": self.tool_options.get("nextpnr_options", [])
            },
        }
        
        yosys = Yosys(self.edam, self.work_root)
        yosys.configure()

        nextpnr = Nextpnr(yosys.edam, self.work_root)
        nextpnr.flow_config = {"arch": "gatemate"}
        nextpnr.configure()

        # Write Makefile
        commands = EdaCommands()
        commands.commands = yosys.commands

        commands.commands += nextpnr.commands

        # Image generation
        depends = self.name + ".txt"
        targets = self.name + ".bit"
        options = " ".join(self.tool_options.get("gmpack_options", ""))
        command = ["gmpack", options, depends, targets]
        commands.add(command, [targets], [depends])

        commands.set_default_target(self.name + ".bit")
        commands.write(os.path.join(self.work_root, "Makefile"))
