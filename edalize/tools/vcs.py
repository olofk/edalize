# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

from pathlib import Path

from edalize.tools.edatool import Edatool
from edalize.utils import EdaCommands


class Vcs(Edatool):

    description = "VCS simulator from Synopsys"

    TOOL_OPTIONS = {
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
    }

    def setup(self, edam):
        super().setup(edam)

        incdirs = []
        vlog_files = []
        unused_files = []
        user_files = []

        vlogan_options = self.tool_options.get("vlogan_options", [])
        vhdlan_options = self.tool_options.get("vhdlan_options", [])
        vcs_options = self.tool_options.get("vcs_options", [])
        run_options = self.tool_options.get("run_options", [])

        include_files = []
        # Get all include dirs first
        for f in self.files.copy():
            file_type = f.get("file_type", "")
            if file_type.startswith("verilogSource") or file_type.startswith(
                "systemVerilogSource"
            ):
                if self._add_include_dir(f, incdirs, force_slash=True):
                    include_files.append(f["name"])
                    self.files.remove(f)

        vlog_include_dirs = ["+incdir+" + d for d in incdirs]

        self.tcl_files = []
        commands = {}
        libs = {}
        # FIXME: consumed files, include files
        for f in self.files:
            lib = f.get("logical_name", "work")

            file_type = f.get("file_type", "")
            if file_type.startswith("verilogSource") or file_type.startswith(
                "systemVerilogSource"
            ):

                vlog_defines = self.vlogdefine.copy()
                vlog_defines.update(f.get("define", {}))

                _args = []
                for k, v in vlog_defines.items():
                    _args.append("+define+{}={}".format(k, self._param_value_str(v)))
                defines = " ".join(_args)
                cmd = "vlogan"
            elif file_type.startswith("vhdlSource"):
                cmd = "vhdlan"
            elif file_type == "tclSource":
                self.tcl_files.append(f["name"])
                cmd = None
            elif file_type == "user":
                user_files.append(f["name"])
                cmd = None
            else:
                unused_files.append(f)
                cmd = None

            if cmd:
                if not lib in libs:
                    libs[lib] = []
                libs[lib].append((cmd, f["name"], defines))
                if not commands.get((cmd, lib, defines)):
                    commands[(cmd, lib, defines)] = []
                commands[(cmd, lib, defines)].append(f["name"])

        # FIXME: Set vhdl/v/sv version
        # FIXME: File-specific defines for include files
        # FIXME: What to do with tcl files?
        self.commands = EdaCommands()
        for lib, files in libs.items():
            cmds = {}
            depfiles = []
            has_vlog = False
            print(lib)
            # Group into individual commands
            for (cmd, fname, defines) in files:
                if not (cmd, defines) in cmds:
                    cmds[(cmd, defines)] = []
                cmds[(cmd, defines)].append(fname)
                depfiles.append(fname)
                if cmd == "vlogan":
                    has_vlog = True
            commands = []
            for (cmd, defines), fnames in cmds.items():
                if cmd == "vlogan":
                    options = vlogan_options.copy()
                    options += [defines]
                    options += vlog_include_dirs
                elif cmd == "vhdlan":
                    options = vhdlan_options.copy()
                if has_vlog:
                    depfiles += include_files
                commands.append([cmd] + options + ["-work", lib] + fnames)
            self.commands.add(commands, [lib], depfiles)

        self.edam = edam.copy()
        self.edam["files"] = unused_files

        _parameters = {**self.vlogparam, **self.generic}
        parameters = []
        for key, value in _parameters.items():
            parameters += [f"-pvalue+{key}=" + self._param_value_str(value)]

        self.commands.add(
            ["vcs", "-o", self.name, "-top", self.toplevel] + vcs_options + parameters,
            [self.name],
            list(libs.keys()) + user_files,
        )

        # FIXME plusargs
        self.commands.add(
            ["./" + self.name],
            ["run"],
            [self.name],
        )
        self.commands.set_default_target(self.name)

    def run(self):
        args = ["run"]

        # Set plusargs
        if self.plusarg:
            plusargs = []
            for key, value in self.plusarg.items():
                plusargs += ["+{}={}".format(key, self._param_value_str(value))]
            args.append("EXTRA_OPTIONS=" + " ".join(plusargs))

        return ("make", args, self.work_root)
