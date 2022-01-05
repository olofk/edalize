# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import os.path

from edalize.edatool import Edatool
from edalize.utils import EdaCommands
from edalize.nextpnr import Nextpnr
from edalize.yosys import Yosys


class Apicula(Edatool):

    argtypes = ["vlogdefine", "vlogparam"]

    @classmethod
    def get_doc(cls, api_ver):
        if api_ver == 0:
            options = {
                "lists": [],
                "members": [
                    {
                        "name": "device",
                        "type": "String",
                        "desc": "Required device option for nextpnr-gowin and gowin_pack command (e.g. GW1N-LV1QN48C6/I5)",
                    },
                ],
            }

            Edatool._extend_options(options, Yosys)
            Edatool._extend_options(options, Nextpnr)

            return {
                "description": "Open source toolchain for Gowin FPGAs. Uses yosys for synthesis and nextpnr for Place & Route",
                "members": options["members"],
                "lists": options["lists"],
            }

    def configure_main(self):
        # Pass apicula tool options to yosys and nextpnr
        self.edam["tool_options"] = {
            "yosys": {
                "arch": "gowin",
                "output_format": "json",
                "yosys_synth_options": [f"-json {self.name}.json"]
                + self.tool_options.get("yosys_synth_options", []),
                "yosys_as_subtool": True,
                "yosys_template": self.tool_options.get("yosys_template"),
            },
            "nextpnr": {
                "device": self.tool_options.get("device"),
                "nextpnr_options": self.tool_options.get("nextpnr_options", []),
            },
        }

        yosys = Yosys(self.edam, self.work_root)
        yosys.configure()

        nextpnr = Nextpnr(yosys.edam, self.work_root)
        nextpnr.flow_config = {"arch": "gowin"}
        nextpnr.configure()

        # Write Makefile
        commands = EdaCommands()
        commands.commands = yosys.commands

        commands.commands += nextpnr.commands

        # Image generation
        depends = self.name + ".pack"
        targets = self.name + ".fs"
        command = [
            "gowin_pack",
            "-d",
            self.tool_options.get("device"),
            "-o",
            targets,
            depends,
        ]
        commands.add(command, [targets], [depends])

        commands.set_default_target(targets)
        commands.write(os.path.join(self.work_root, "Makefile"))
