# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import logging
import os.path

from edalize.tools.edatool import Edatool
from edalize.utils import EdaCommands

logger = logging.getLogger(__name__)


class Icepack(Edatool):

    description = "Generate binary image for iCE40 FPGAs"

    TOOL_OPTIONS = {
        "icepack_options": {
            "type": "str",
            "desc": "Additional options for icepack",
            "list": True,
        }
    }

    def setup(self, edam):
        super().setup(edam)

        unused_files = []

        asc_file = ""
        bin_file = ""
        for f in self.files:
            if f.get("file_type") == "iceboxAscii":
                if asc_file:
                    raise RuntimeError(
                        "Icepack only supports one input file. Found {} and {}".format(
                            asc_file, f["name"]
                        )
                    )
                asc_file = f["name"]
            else:
                unused_files.append(f)

        if not asc_file:
            raise RuntimeError("No input file specified for icepack")

        bin_file = os.path.splitext(asc_file)[0] + ".bin"
        self.edam = edam.copy()
        self.edam["files"] = unused_files
        self.edam["files"].append({"name": bin_file, "file_type": "binary"})

        # Image generation
        depends = asc_file
        targets = bin_file
        command = (
            ["icepack"]
            + self.tool_options.get("icepack_options", [])
            + [depends, targets]
        )

        commands = EdaCommands()
        commands.add(command, [targets], [depends])
        commands.set_default_target(bin_file)
        self.commands = commands
