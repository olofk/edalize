# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import logging
import os.path

from edalize.tools.edatool import Edatool
from edalize.utils import EdaCommands

logger = logging.getLogger(__name__)


class Icetime(Edatool):

    description = "Static timing analysis for iCE40 FPGAs"

    TOOL_OPTIONS = {
        "icetime_options": {
            "type": "str",
            "desc": "Additional options for icetime",
            "list": True,
        }
    }

    def setup(self, edam):
        super().setup(edam)
        unused_files = []

        asc_file = ""
        for f in self.files:
            if f.get("file_type") == "iceboxAscii":
                if asc_file:
                    raise RuntimeError(
                        "Icetime only supports one input file. Found {} and {}".format(
                            asc_file, f["name"]
                        )
                    )
                asc_file = f["name"]
            else:
                unused_files.append(f)

        if not asc_file:
            raise RuntimeError("No input file specified for icetime")

        tim_file = os.path.splitext(asc_file)[0] + ".tim"
        self.edam["files"] = unused_files
        self.edam["files"].append({"name": tim_file, "file_type": "report"})

        # Image generation
        depends = asc_file
        targets = tim_file
        command = ["icetime", "-r", targets] + self.tool_options.get(
            "icetime_options", []
        )
        command.append(depends)

        commands = EdaCommands()
        commands.add(command, [targets], [depends])
        commands.add([], ["timing"], [targets])
        commands.set_default_target("timing")
        self.commands = commands
