# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import logging

from edalize.tools.edatool import Edatool
from edalize.utils import EdaCommands

logger = logging.getLogger(__name__)


class Xcelium(Edatool):
    description = "Xcelium (xrun) simulator from Cadence"

    TOOL_OPTIONS = {
        "32bit": {
            "type": "bool",
            "desc": "Disable 64-bit mode",
        },
        "timescale": {"type": "str", "desc": "Default timescale for simulation"},
        "xrun_options": {"type": "str", "desc": "Additional run options for xrun"},
    }

    V_SRC_FILE_TYPES = ["verilogSource", "systemVerilogSource"]
    TCL_SCRIPT_TYPES = ["tclSource"]
    DPIC_LIB_TYPES = ["dpiLibrary"]

    def setup(self, edam):
        super().setup(edam)

        self.commands = EdaCommands()

        unused_files = self.files.copy()
        incdirs = []
        include_files = []
        src_files = []
        tcl_files = []
        dpi_libraries = []
        has_system_verilog = False

        # Move different type of files to a separate list
        for f in self.files:
            # Skip any file that is not tagged for simulation
            if not "simulation" in f.get("tags", ["simulation"]):
                continue

            file_type = f.get("file_type", "")

            # Verilog source files
            if file_type in self.V_SRC_FILE_TYPES:
                if self._add_include_dir(f, incdirs, force_slash=True):
                    # This file is a include file
                    include_files.append(f["name"])
                else:
                    if file_type.startswith("systemVerilogSource"):
                        has_system_verilog = True

                    # This file is a normal source file
                    src_files.append(f["name"])
                unused_files.remove(f)

            if file_type in self.TCL_SCRIPT_TYPES:
                tcl_files.append(f["name"])
                unused_files.remove(f)

            if file_type in self.DPIC_LIB_TYPES:
                dpi_libraries.append(f["name"])
                unused_files.remove(f)

        self.edam = edam.copy()
        self.edam["files"] = unused_files

        all_files = src_files + include_files + tcl_files + dpi_libraries
        self.src_files = src_files

        # Append option flags
        en_64bit_cmd = [] if self.tool_options.get("32bit") else ["-64bit"]
        sv_cmd = ["-sv"] if has_system_verilog else []

        # Append timescale option
        timescale_cmd = (
            ["-timescale", self.tool_options.get("timescale")]
            if self.tool_options.get("timescale")
            else []
        )

        # Append TCL scripts
        tcl_cmd = []
        for tcl in tcl_files:
            tcl_cmd.append(["-input", tcl])

        # Append DPI libraries
        dpi_lib_cmd = []
        for lib in dpi_libraries:
            dpi_lib_cmd.append(["-sv_lib", lib])

        # Append macro definitions
        macro_def_cmd = []
        for k, v in self.vlogdefine.items():
            macro_def_cmd.append(
                "+define+{}={}".format(
                    k, self._param_value_str(v, str_quote_style='""')
                )
            )

        # Append include directories
        incdir_cmd = ["+incdir+" + d for d in incdirs]

        # Append top level module
        top_cmd = ["-top", self.toplevel]

        # Prepare the simulation command
        self.commands.add(
            ["xrun"]
            + en_64bit_cmd
            + sv_cmd
            + timescale_cmd
            + tcl_cmd
            + dpi_lib_cmd
            + macro_def_cmd
            + incdir_cmd
            + top_cmd
            + ["-f", "xrun.f"]
            + self.tool_options.get("xrun_options", []),
            ["run"],
            include_files + tcl_files + dpi_libraries + ["xrun.f"],
        )

        self.commands.set_default_target("run")

    def write_config_files(self):
        # Update f files to include all sources
        self.update_config_file("xrun.f", "\n".join(self.src_files) + "\n")

    def run(self):
        args = ["run"]

        # Set plusargs
        if self.plusarg:
            plusargs = []
            for key, value in self.plusarg.items():
                plusargs += ["+{}={}".format(key, self._param_value_str(value))]
            args.append("EXTRA_OPTIONS=" + " ".join(plusargs))

        return ("make", args, self.work_root)
