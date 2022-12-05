# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import os.path
import re

from edalize.edatool import Edatool
from edalize.utils import EdaCommands
from edalize.yosys import Yosys


class Gatemate(Edatool):

    argtypes = ["vlogdefine", "vlogparam"]

    @classmethod
    def get_doc(cls, api_ver):
        if api_ver == 0:
            options = {
                "lists": [
                    {
                        "name": "p_r_options",
                        "type": "string",
                        "desc": "Additional option for p_r",
                    },
                ],
                "members": [
                    {
                        "name": "device",
                        "type": "String",
                        "desc": "Required device option for p_r command (e.g. CCGM1A1)",
                    },
                ],
            }

            Edatool._extend_options(options, Yosys)

            return {
                "description": "backend for CologneChip GateMate.",
                "members": options["members"],
                "lists": options["lists"],
            }

    def configure_main(self):
        (src_files, incdirs) = self._get_fileset_files()
        synth_out = self.name + "_synth.v"

        device = self.tool_options.get("device")
        if not device:
            raise RuntimeError("Missing required option 'device' for p_r")

        match = re.search("^CCGM1A([1-9]{1,2})$", device)
        if not match:
            raise RuntimeError("{} is not known device name".format(device))

        device_number = match.groups()[0]
        if device_number not in ["1", "2", "4", "9", "16", "25"]:
            raise RuntimeError("Rel. size {} is not unsupported".format(device_number))

        ccf_file = None

        for f in src_files:
            if f.file_type == "CCF":
                if ccf_file:
                    raise RuntimeError(
                        "p_r only supports one ccf file. Found {} and {}".format(
                            ccf_file, f.name
                        )
                    )
                else:
                    ccf_file = f.name

        # Pass trellis tool options to yosys
        self.edam["tool_options"] = {
            "yosys": {
                "arch": "gatemate",
                "output_format": "verilog",
                "output_name": synth_out,
                "yosys_synth_options": self.tool_options.get("yosys_synth_options", []),
                "yosys_as_subtool": True,
                "yosys_template": self.tool_options.get("yosys_template"),
            },
        }

        yosys = Yosys(self.edam, self.work_root)
        yosys.configure()

        # Write Makefile
        commands = EdaCommands()
        commands.commands = yosys.commands

        # PnR & image generation
        targets = self.name + "_00.cfg.bit"
        command = [
            "p_r",
            "-A",
            device_number,
            "-i",
            synth_out,
            "-o",
            self.name,
            "-lib",
            "ccag",
            " ".join(self.tool_options.get("p_r_options", "")),
        ]
        if ccf_file is not None:
            command += ["-ccf", ccf_file]
        commands.add(command, [targets], [synth_out])

        commands.set_default_target(targets)
        commands.write(os.path.join(self.work_root, "Makefile"))
