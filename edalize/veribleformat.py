# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

from __future__ import annotations

import logging
import re
import os
import subprocess

from edalize.edam import ToolDoc
from edalize.edatool import Edatool

logger = logging.getLogger(__name__)


class Veribleformat(Edatool):

    argtypes = ["vlogdefine", "vlogparam"]

    @classmethod
    def get_doc(cls, api_ver: int) -> ToolDoc | None:
        if api_ver == 0:
            return {
                "description": "Verible format backend (verible-verilog-format)",
                "lists": [
                    {
                        "name": "verible_format_args",
                        "type": "String",
                        "desc": "Extra command line arguments passed to the Verible tool",
                    },
                ],
            }
        return None

    def build_main(self, target: str | None = None) -> None:
        pass

    def _get_tool_args(self) -> list[str]:
        args = []
        if "verible_format_args" in self.tool_options:
            args += self.tool_options["verible_format_args"]

        return args

    def run_main(self) -> None:
        (src_files, incdirs) = self._get_fileset_files(force_slash=True)

        src_files_filtered = []
        for src_file in src_files:
            ft = src_file.file_type
            if not ft.startswith("verilogSource") and not ft.startswith(
                "systemVerilogSource"
            ):
                continue
            src_files_filtered.append(src_file.name)

        if len(src_files_filtered) == 0:
            logger.warning("No SystemVerilog source files to be processed.")
            return

        fail = False
        for src_file in src_files_filtered:
            cmd = ["verible-verilog-format"] + self._get_tool_args() + [src_file]
            logger.debug("Running " + " ".join(cmd))

            try:
                res = subprocess.run(cmd, cwd=self.work_root, check=False)
            except FileNotFoundError:
                _s = "Command '{}' not found. Make sure it is in $PATH"
                raise RuntimeError(_s.format(cmd[0]))

            if res.returncode != 0:
                fail = True
        if fail:
            raise RuntimeError("Verible returned a non-zero exit code.")
