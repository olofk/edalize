# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

from edalize.tools.edatool import Edatool
from edalize.utils import EdaCommands


class Openfpgaloader(Edatool):

    description = "openFPGALoader, a universal utility for programming FPGAs"

    TOOL_OPTIONS = {
        "openfpgaloader_options": {
            "type": "str",
            "desc": "Additional options for openFPGALoader",
            "list": True,
        },
        "board": {
            "type": "str",
            "desc": "Target board to program",
        },
    }

    def setup(self, edam):
        super().setup(edam)

        unused_files = []
        board = self.tool_options.get("board", "")

        bit_file = ""
        for f in self.files:
            if f.get("file_type") == "gowinFusesFile":
                if bit_file:
                    raise RuntimeError(
                        "openFPGAloader only supports one input file. Found {} and {}".format(
                            bit_file, f["name"]
                        )
                    )
                bit_file = f["name"]
            else:
                unused_files.append(f)

        if not bit_file:
            raise RuntimeError("No input file specified for openFPGAloader")

        self.edam = edam.copy()
        self.edam["files"] = unused_files

        # Programmer
        depends = bit_file
        targets = "openfpgaloader"
        board = ["-b", board] if board else []
        command = (
            ["openFPGALoader"]
            + board
            + self.tool_options.get("openfpgaloader_options", [])
            + [depends]
        )

        commands = EdaCommands()
        commands.add(command, [targets], [depends])
        commands.set_default_target(targets)
        self.commands = commands
