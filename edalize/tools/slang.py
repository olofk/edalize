# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import logging

from edalize.tools.edatool import Edatool
from edalize.utils import EdaCommands

logger = logging.getLogger(__name__)


class Slang(Edatool):
    description: str = "The slang suite of system verilog tools."

    slang_tidy_args: list[str] = []
    slang_tidy_arg_file: str = "slang_tidy_arguments"

    commands: EdaCommands = EdaCommands()

    TOOL_OPTIONS = {
        "slang_tool": {
            "type": "str",
            "desc": "The slang tool to use. Currently the only supported tool is slang_tidy.",
        },
        "slang_tidy_options": {
            "type": "str",
            "desc": "Additional arguments to provide to the slang-tidy tool",
            "list": True,
        },
    }

    def setup(self, edam):
        super().setup(edam)

        slang_tool = self.tool_options.get("slang_tool", "slang_tidy")
        if slang_tool != "slang_tidy":
            raise RuntimeError("Currently the only supported tool is slang_tidy.")

        system_verilog_files = [
            f_name
            for (f_name, f_type) in (
                (file["name"], file.get("file_type", "")) for file in self.files
            )
            if f_type.startswith("systemVerilogSource")
            or f_type.startswith("verilogSource")
        ]

        self.slang_tidy_args = (
            [f"--top {self.toplevel}"]
            + system_verilog_files
            + self.tool_options.get("slang_tidy_options", [])
        )

        default_target = "slang_tidy"
        self.commands.set_default_target(default_target)
        self.commands.add(
            ["slang-tidy", "-f", self.slang_tidy_arg_file],
            [default_target],
            system_verilog_files + [self.slang_tidy_arg_file],
        )

    def write_config_files(self):
        self.update_config_file(
            self.slang_tidy_arg_file, "\n".join(self.slang_tidy_args) + "\n"
        )
