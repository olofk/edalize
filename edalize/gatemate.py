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
                        "name": "nextpnr_options",
                        "type": "string",
                        "desc": "Additional option for nextpnr",
                    },
                ],
                "members": [
                    {
                        "name": "device",
                        "type": "String",
                        "desc": "Required device option for nextpnr command (e.g. CCGM1A1)",
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
        synth_out = self.name + ".json"

        device = self.tool_options.get("device")
        if not device:
            raise RuntimeError("Missing required option 'device' for nextpnr")

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
                        "nextpnr only supports one ccf file. Found {} and {}".format(
                            ccf_file, f.name
                        )
                    )
                else:
                    ccf_file = f.name

        # nextpnr_log_file = None
        nextpnr_log_file = "nextpnr.log"

        # Pass GateMate tool options to yosys
        self.edam["tool_options"] = {
            "yosys": {
                "arch": "gatemate",
                "output_format": "json",
                "output_name": synth_out,
                "yosys_synth_options": self.tool_options.get("yosys_synth_options", []),
                "yosys_as_subtool": True,
                "yosys_template": self.tool_options.get("yosys_template"),
            },
        }

        yosys = Yosys(self.edam, self.work_root)

        # Always define CCGM
        yosys.vlogdefine["CCGM"] = 1

        for k, v in self.tool_options.get("vlogdefine", []):
            yosys.vlogdefine[k] = v

        for k, v in self.tool_options.get("vlogparam", []):
            yosys.vlogparam[k] = v

        yosys.configure_main()

        # Write Makefile
        commands = EdaCommands()
        commands.commands = yosys.commands

        # nextpnr & image generation
        commands.add_var("NEXTPNR := $(shell which nextpnr-himbaechel)")
        cfg_target = self.name + ".cfg"
        command = [
            "$(NEXTPNR)",
            "--device",
            device,
            "--json",
            "$<",
            "-o out=" + cfg_target,
            " ".join(self.tool_options.get("nextpnr_options", "")),
        ]
        if ccf_file is not None:
            command += ["-o ccf=" + ccf_file]

        if nextpnr_log_file is not None:
            command += ["--log", nextpnr_log_file]

        commands.add(command, [cfg_target], [synth_out])

        commands.add_var("GMPACK := $(shell which gmpack)")
        bit_target = self.name + ".bit"
        command = [
            "$(GMPACK) $< $@",
        ]
        commands.add(command, [bit_target], [cfg_target])

        commands.set_default_target(bit_target)
        commands.write(os.path.join(self.work_root, "Makefile"))
