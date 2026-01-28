# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

from edalize.tools.edatool import Edatool
from edalize.utils import EdaCommands

class Gmpack(Edatool):

    description = "Generate binary image for GateMate FPGAs"

    TOOL_OPTIONS = {
        "gmpack_options": {
            "type": "str",
            "desc": "Additional options for gmpack",
            "list": True,
        },
    }

    def setup(self, edam):
        super().setup(edam)

        unused_files = []
        bit_file = self.edam["name"] + ".bit"
        gmcfg_file = ""
        for f in self.files:
            if f.get("file_type") == "gatemateConfig":
                if gmcfg_file:
                    raise RuntimeError(
                        "gmpack only supports one input file. Found {} and {}".format(
                            gmcfg_file, f["name"]
                        )
                    )
                gmcfg_file = f["name"]
            else:
                unused_files.append(f)

        if not gmcfg_file:
            raise RuntimeError("No input file specified for gmpack")

        self.edam = edam.copy()
        self.edam["files"] = unused_files
        self.edam["files"].append({"name": bit_file, "file_type": "gatemateBitFile"})

        # Image generation
        depends = gmcfg_file
        targets = bit_file
        command = (
            ["gmpack"]
            + self.tool_options.get("gmpack_options", [])
            + [depends, targets]
        )

        commands = EdaCommands()
        commands.add(command, [targets], [depends])
        commands.set_default_target(targets)
        self.commands = commands
