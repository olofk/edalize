# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import logging
from pathlib import Path

from edalize.tools.edatool import Edatool
from edalize.utils import EdaCommands

logger = logging.getLogger(__name__)


class Vcs(Edatool):

    description = "VCS simulator from Synopsys"

    TOOL_OPTIONS = {
        "32bit": {
            "type": "bool",
            "desc": "Disable 64-bit mode",
        },
        "2_stage_flow": {
            "type": "bool",
            "desc": "Run VCS in 2-stage (elaborate+compile => simulate) instead of 3-stage mode (elaborate => compile => simulate)",
        },
        "analysis_options": {
            "type": "str",
            "desc": "Options that are passed to vcs in 2-stage mode or vhdlan/vlogan in 3-stage mode",
            "list": True,
        },
        "vlogan_options": {
            "type": "str",
            "desc": "Additional options for analysis with vlogan",
            "list": True,
        },
        "vhdlan_options": {
            "type": "str",
            "desc": "Additional options for analysis with vhdlan",
            "list": True,
        },
        "vcs_options": {
            "type": "str",
            "desc": "Additional options for elaboration with vcs",
            "list": True,
        },
        "run_options": {
            "type": "str",
            "desc": "Additional run-time options for the simulation",
            "list": True,
        },
        "binary_name": {
            "type": "str",
            "desc": "Set name of the simulation binary (defaults to system name)",
        },
    }

    def setup(self, edam):
        super().setup(edam)

        self.commands = EdaCommands()
        self.f_files = {}
        self.workdirs = set()
        self.target_files = []
        self.user_files = []

        incdirs = []
        include_files = []
        unused_files = self.files.copy()
        # Get all include dirs. Move include files to a separate list
        for f in self.files:
            if not "simulation" in f.get("tags", ["simulation"]):
                continue
            file_type = f.get("file_type", "")
            if file_type.startswith("verilogSource") or file_type.startswith(
                "systemVerilogSource"
            ):
                if self._add_include_dir(f, incdirs, force_slash=True):
                    include_files.append(f["name"])
                    unused_files.remove(f)

        full64 = [] if self.tool_options.get("32bit") else ["-full64"]
        if self.tool_options.get("2_stage_flow"):
            self._twostage_setup(edam, incdirs, include_files, unused_files, full64)
        else:
            self._threestage_setup(edam, incdirs, include_files, unused_files, full64)

        self.edam = edam.copy()
        self.edam["files"] = unused_files

        binary_name = self.tool_options.get("binary_name", self.name)
        self.commands.add(
            ["vcs"]
            + full64
            + ["-o", binary_name, "-file", "vcs.f", "-parameters", "parameters.txt"]
            + self.vcs_files,
            [binary_name],
            self.target_files + self.user_files + ["vcs.f", "parameters.txt"],
        )

        self.commands.add(
            ["./" + binary_name, "$(EXTRA_OPTIONS)"]
            + self.tool_options.get("run_options", []),
            ["run"],
            [],
        )
        self.commands.set_default_target(binary_name)

    def _twostage_setup(self, edam, incdirs, include_files, unused_files, full64):

        user_files = []

        vlog_files = []

        c_files = []

        has_sv = False
        for f in unused_files.copy():
            if not "simulation" in f.get("tags", ["simulation"]):
                continue

            fname = f.get("name")

            file_type = f.get("file_type", "")
            if file_type.startswith("verilogSource") or file_type.startswith(
                "systemVerilogSource"
            ):

                if file_type.startswith("systemVerilogSource"):
                    has_sv = True

                vlog_files.append(fname)
                unused_files.remove(f)
            elif file_type.startswith("vhdlSource"):
                logger.warning(
                    f"Only (system)Verilog supported in two-stage mode. Ignoring VHDL file {fname}"
                )
            elif file_type == "user":
                user_files.append(f["name"])
            elif file_type == "cSource":
                c_files.append(fname)
                unused_files.remove(f)

            if f.get("define"):
                logger.warning(
                    f"File-specific defines not supported in two-stage mode. Ignoring {fname}"
                )

        _args = []
        for k, v in self.vlogdefine.items():
            _args.append(
                "+define+{}={}".format(
                    k, self._param_value_str(v, str_quote_style='""')
                )
            )
        defines = " ".join(_args)

        options = ["-top", self.toplevel]
        if has_sv:
            options.append("-sverilog")
        options += self.tool_options.get("analysis_options", [])
        options += self.tool_options.get("vcs_options", [])
        options += [defines]
        options += ["+incdir+" + d for d in incdirs]

        self.f_files["vcs.f"] = options

        self.target_files = include_files + vlog_files + c_files
        self.vcs_files = vlog_files + c_files

    def _threestage_setup(self, edam, incdirs, include_files, unused_files, full64):
        filegroups = []
        c_files = []
        prev_fileopts = ("", "", "")  # file_type, logical_name, defines
        for f in unused_files.copy():
            lib = f.get("logical_name", "work")

            file_type = f.get("file_type", "")
            if file_type.startswith("verilogSource") or file_type.startswith(
                "systemVerilogSource"
            ):

                vlog_defines = self.vlogdefine.copy()
                vlog_defines.update(f.get("define", {}))

                _args = []
                for k, v in vlog_defines.items():
                    _args.append(
                        "+define+{}={}".format(
                            k, self._param_value_str(v, str_quote_style='""')
                        )
                    )
                defines = " ".join(_args)
                cmd = "vlogan"
            elif file_type.startswith("vhdlSource"):
                cmd = "vhdlan"
            elif file_type == "user":
                self.user_files.append(f["name"])
                cmd = None
            elif file_type == "cSource":
                c_files.append(f["name"])
                cmd = None
            else:
                cmd = None

            if not "simulation" in f.get("tags", ["simulation"]):
                cmd = None

            # Iterate over all relevant source files. If a file has
            # different file_type, logical_name or defines compared
            # to the previous file, we put it in a new file group
            if cmd:
                fileopts = (cmd, file_type, lib, defines)
                if fileopts != prev_fileopts:
                    filegroups.append((fileopts, []))
                filegroups[-1][1].append(f["name"])
                unused_files.remove(f)
                prev_fileopts = fileopts

        cmds = []
        depfiles = []
        for fg in filegroups:
            # Ignore empty file groups
            if fg[1]:
                (cmd, file_type, lib, defines) = fg[0]
                depfiles += fg[1]
                options = self.tool_options.get("analysis_options", []).copy()
                if cmd == "vlogan":
                    if file_type.startswith("systemVerilogSource"):
                        options.append("-sverilog")
                    options += self.tool_options.get("vlogan_options", [])
                    options += [defines]
                    options += ["+incdir+" + d for d in incdirs]
                    target_file = f"{lib}.workdir/AN.DB/make.vlogan"
                    depfiles += include_files
                elif cmd == "vhdlan":
                    options += self.tool_options.get("vhdlan_options", [])
                    target_file = f"{lib}.workdir/64/vhmra.sdb"

                # Find a free name for a f file and log file
                f_file = lib + ".f"
                libsuffix = f"{lib}"
                suffix = ""
                i = 0
                if f_file in self.f_files:
                    while f_file in self.f_files:
                        i += 1
                        libsuffix = f"{lib}_{i}"
                        f_file = f"{libsuffix}.f"
                logfile = f"{libsuffix}.log"

                self.f_files[f_file] = options

                self.workdirs.add(lib)

                if not target_file in self.target_files:
                    self.target_files.append(target_file)

                cmds.append(
                    [cmd]
                    + full64
                    + ["-file", f_file, "-work", lib, "-l", logfile]
                    + fg[1]
                )

        self.commands.add(cmds, self.target_files, depfiles + list(self.f_files.keys()))

        self.f_files["vcs.f"] = (
            ["-top", self.toplevel] + self.tool_options.get("vcs_options", []) + c_files
        )
        self.vcs_files = []

    def write_config_files(self):
        s = "WORK > DEFAULT\nDEFAULT : ./work.workdir\n"
        for lib in self.workdirs:
            if lib != "work":
                s += f"{lib} : ./{lib}.workdir\n"
        self.update_config_file("synopsys_sim.setup", s)
        for k, v in self.f_files.items():
            self.update_config_file(k, " ".join(v) + "\n")

        _parameters = {**self.vlogparam, **self.generic}
        s = ""
        for key, value in _parameters.items():
            _value = self._param_value_str(value, '"')
            s += f"assign {_value} {key}\n"
        self.update_config_file("parameters.txt", s)

    def run(self):
        args = ["run"]

        # Set plusargs
        if self.plusarg:
            plusargs = []
            for key, value in self.plusarg.items():
                plusargs += ["+{}={}".format(key, self._param_value_str(value))]
            args.append("EXTRA_OPTIONS=" + " ".join(plusargs))

        return ("make", args, self.work_root)
