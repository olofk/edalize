# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

from edalize.tools.edatool import Edatool
from edalize.utils import EdaCommands


class Ecppack(Edatool):

    description = "Generate binary image for ECP5 FPGAs"

    TOOL_OPTIONS = {
        "ecppack_options": {
            "type": "str",
            "desc": "Additional options for ecppack",
            "list": True,
        }
    }

    def setup(self, edam):
        super().setup(edam)

        unused_files = []

        config_file = ""
        bit_file = ""

        for f in self.files:
            if f.get("file_type") == "nextpnrTrellisConfig":
                if config_file:
                    raise RuntimeError(
                        "ecppack only supports one input file. Found {} and {}".format(
                            config_file, f["name"]
                        )
                    )
                config_file = f["name"]
            else:
                unused_files.append(f)

        if not config_file:
            raise RuntimeError("No input file specified for ecppack")

        bit_file = self.edam["name"] + ".bit"
        self.edam = edam.copy()
        self.edam["files"] = unused_files
        self.edam["files"].append({"name": bit_file, "file_type": "bitstream"})

        # Image generation
        depends = config_file
        targets = bit_file
        command = (
            ["ecppack"]
            + self.tool_options.get("ecppack_options", [])
            + [depends, targets]
        )

        commands = EdaCommands()
        commands.add(command, [targets], [depends])
        commands.set_default_target(bit_file)
        self.commands = commands
