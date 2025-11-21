# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import logging
from os import path

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

        sv_files = [
            file
            for file in self.files
            if file.get("file_type", "").startswith("systemVerilogSource")
            or file.get("file_type", "").startswith("verilogSource")
        ]

        sv_include_directories: set[str] = {
            file.get("include_path") or path.dirname(file["name"]) or "."
            for file in sv_files
            if file.get("is_include_file", False)
        }

        sv_noninclude_filenames = [
            file["name"] for file in sv_files if not file.get("is_include_file", False)
        ]

        sv_filenames = [file["name"] for file in sv_files]

        self.slang_tidy_args = (
            [f"--top {self.toplevel}"]
            + [f"-I {dir}" for dir in sv_include_directories]
            + sv_noninclude_filenames
            + self.tool_options.get("slang_tidy_options", [])
        )

        default_target = "slang_tidy"
        self.commands.set_default_target(default_target)
        self.commands.add(
            ["slang-tidy", "-f", self.slang_tidy_arg_file],
            [default_target],
            sv_filenames + [self.slang_tidy_arg_file],
        )

    def write_config_files(self):
        self.update_config_file(
            self.slang_tidy_arg_file, "\n".join(self.slang_tidy_args) + "\n"
        )
