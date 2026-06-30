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
        "xrun_options": {
            "type": "str",
            "desc": "Additional run options for xrun",
            "list": True,
        },
        "gui": {"type": "bool", "desc": "Invoke the Graphical User Interface (GUI)"},
    }

    V_SRC_FILE_TYPES = ["verilogSource", "systemVerilogSource"]
    TCL_SCRIPT_TYPES = ["tclSource"]
    DPIC_LIB_TYPES = ["dpiLibrary"]

    #: Map file type to xrun argument that will enable particular Verilog or VHDL features
    FILE_TYPE_TO_FEATURE_FLAG = {
        "verilogSource-95": "-v1995",
        "verilogSource-1995": "-v1995",
        "verilogSource-2001": "-v2001",
        "vhdlSource-93": "-v93",
        "vhdlSource-1993": "-v93",
        "vhdlSource-2008": "-v200x",
        "vhdlSource-2019": "-v2019",
    }

    def setup(self, edam):
        super().setup(edam)

        self.commands = EdaCommands()

        unused_files = self.files.copy()
        incdirs = []
        include_files = []
        src_files = []
        tcl_files = []
        dpi_libraries = []

        # Move different type of files to a separate list
        for f in self.files:
            # Skip any file that is not tagged for simulation
            if not "simulation" in f.get("tags", ["simulation"]):
                continue

            file_type = f.get("file_type", "")

            # Verilog source files
            if any(map(file_type.startswith, self.V_SRC_FILE_TYPES)):
                if self._add_include_dir(f, incdirs, force_slash=True):
                    # This file is a include file
                    include_files.append(f["name"])
                else:
                    # This file is a normal source file
                    src_files.append(f)
                unused_files.remove(f)

            if file_type.startswith("vhdlSource"):
                src_files.append(f)
                unused_files.remove(f)

            if file_type in self.TCL_SCRIPT_TYPES:
                tcl_files.append(f["name"])
                unused_files.remove(f)

            if file_type in self.DPIC_LIB_TYPES:
                dpi_libraries.append(f["name"])
                unused_files.remove(f)

        self.edam = edam.copy()
        self.edam["files"] = unused_files

        # Append option flags
        en_64bit_cmd = [] if self.tool_options.get("32bit") else ["-64bit"]

        # Append timescale option
        timescale_cmd = (
            ["-timescale", self.tool_options.get("timescale")]
            if self.tool_options.get("timescale")
            else []
        )

        # Append TCL scripts
        self.tcl_cmd = []
        for tcl in tcl_files:
            self.tcl_cmd += ["-input", tcl]

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

        # Append Verilog parameters
        vlogparam_cmd = []
        for k, v in self.vlogparam.items():
            val = self._param_value_str(v, str_quote_style='"')
            vlogparam_cmd.append(f"-defparam {self.toplevel}.{k}={val}")

        # Append include directories
        incdir_cmd = ["+incdir+" + d for d in incdirs]

        # Append top level module
        top_cmd = ["-top", self.toplevel]

        prev_fileopts = ("", "", {})
        filegroups = []
        # Iterate over all relevant source files. If a file has
        # different file_type, logical_name or defines compared
        # to the previous file, we put it in a new file group
        for f in src_files:
            # The 'worklib' is the default library in Xcelium
            # We need to use -makelib <library> <option>... <file>... -endlib to group files
            # This is required to support compiling mixed-languages and mixed-standards altogether
            lib = f.get("logical_name", "worklib")
            defines = f.get("define", {})
            file_type = f.get("file_type")
            fileopts = (file_type, lib, defines)
            if fileopts != prev_fileopts:
                filegroups.append((fileopts, []))
            filegroups[-1][1].append(f["name"])
            prev_fileopts = fileopts

        files_cmd = []
        for fg in filegroups:
            # Ignore empty file groups
            if fg[1]:
                (file_type, lib, defines) = fg[0]
                if lib:
                    files_cmd += ["-makelib", lib]
                for k, v in defines.items():
                    files_cmd += ["-define", f"{k}={v}"]
                if file_type.startswith("systemVerilogSource"):
                    files_cmd += ["-sv"]
                if file_type in self.FILE_TYPE_TO_FEATURE_FLAG:
                    files_cmd += [self.FILE_TYPE_TO_FEATURE_FLAG[file_type]]
                files_cmd += fg[1]
                if lib:
                    files_cmd += ["-endlib"]

        # This file seems to only be created after a successful build
        target = "xcelium.d/run.d/hdl.var"

        # Prepare the simulation command
        # -enable_cmdline_define_redefinition is required to support file-specific defines
        self.commands.add(
            [
                "xrun",
                "-elaborate",
                "-f",
                "xrun.f",
                "-enable_cmdline_define_redefinition",
            ]
            + files_cmd,
            [target],
            [f["name"] for f in src_files]
            + include_files
            + tcl_files
            + dpi_libraries
            + ["xrun.f"],
        )

        self.xrun_f = (
            en_64bit_cmd
            + dpi_lib_cmd
            + macro_def_cmd
            + vlogparam_cmd
            + incdir_cmd
            + top_cmd
            + self.tool_options.get("xrun_options", [])
        )
        self.commands.set_default_target(target)

    def write_config_files(self):
        print(self.xrun_f)
        # Keep all command-line options in xrun.f to detect build config changes
        self.update_config_file("xrun.f", "\n".join(self.xrun_f) + "\n")

    def run(self):
        args = ["-R"] + self.tcl_cmd

        if self.tool_options.get("gui"):
            args += ["-gui"]

        # Set plusargs
        if self.plusarg:
            plusargs = []
            for key, value in self.plusarg.items():
                plusargs += ["+{}={}".format(key, self._param_value_str(value))]
            args += plusargs

        return ("xrun", args, self.work_root)
