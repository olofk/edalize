# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

from pathlib import Path

from edalize.tools.edatool import Edatool
from edalize.utils import EdaCommands


class Modelsim(Edatool):

    description = "ModelSim/QuestaSim simulator from Siemens EDA"

    TOOL_OPTIONS = {
        "vcom_options": {
            "type": "str",
            "desc": "Additional options for compilation with vcom",
            "list": True,
        },
        "vlog_options": {
            "type": "str",
            "desc": "Additional options for compilation with vlog",
            "list": True,
        },
        "vsim_options": {
            "type": "str",
            "desc": "Additional run options for vsim",
            "list": True,
        },
    }

    def setup(self, edam):
        super().setup(edam)

        incdirs = []
        include_files = []
        unused_files = self.files.copy()

        vlog_options = self.tool_options.get("vlog_options", [])
        vcom_options = self.tool_options.get("vcom_options", [])
        vsim_options = self.tool_options.get("vsim_options", [])

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

        user_files = []
        vlog_include_dirs = ["+incdir+" + d for d in incdirs]

        self.tcl_files = []
        self.tcl_main = []
        self.tcl_build_rtl = []
        commands = {}
        libs = {}
        # FIXME: vlib, -sv, langver, mfcu
        for f in unused_files.copy():
            lib = f.get("logical_name", "work")

            langver = ""

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
                            k, self._param_value_str(v, str_quote_style='\\"')
                        )
                    )
                defines = " ".join(_args)
                cmd = "vlog"
            elif file_type.startswith("vhdlSource"):
                if file_type.endswith("-87"):
                    langver = "-87"
                if file_type.endswith("-93"):
                    langver = "-93"
                if file_type.endswith("-2008"):
                    langver = "-2008"
                cmd = "vcom"
            elif file_type == "tclSource":
                self.tcl_files.append(f["name"])
                cmd = None
            elif file_type == "user":
                user_files.append(f["name"])
                cmd = None
            else:
                cmd = None

            if not "simulation" in f.get("tags", ["simulation"]):
                cmd = None

            if cmd:
                if not lib in libs:
                    libs[lib] = []
                libs[lib].append((cmd, f["name"], defines, langver))
                if not commands.get((cmd, lib, defines, langver)):
                    commands[(cmd, lib, defines, langver)] = []
                commands[(cmd, lib, defines, langver)].append(f["name"])
                unused_files.remove(f)

        self.commands = EdaCommands()
        for lib, files in libs.items():
            cmds = {}
            depfiles = []
            has_vlog = False
            # Group into individual commands
            for (cmd, fname, defines, langver) in files:
                if not (cmd, defines, langver) in cmds:
                    cmds[(cmd, defines, langver)] = []
                cmds[(cmd, defines, langver)].append(fname)
                depfiles.append(fname)
                if cmd == "vlog":
                    has_vlog = True
            commands = [["vlib", lib]]
            i = 1
            f_files = {}
            for (cmd, defines, langver), fnames in cmds.items():
                options = []
                if cmd == "vlog":
                    if has_sv:
                        options.append("-sverilog")
                    options += self.tool_options.get("vlog_options", [])
                    options += [defines]
                    options += ["+incdir+" + d for d in incdirs]
                elif cmd == "vcom":
                    options += self.tool_options.get("vcom_options", [])
                    if langver:
                        options.append(langver)
                f_file = f"{lib}.{i}.f"
                f_files[f_file] = options
                i += 1
                commands.append([cmd, "-f", f_file, "-work", lib] + fnames)
            if has_vlog:
                depfiles += include_files
            self.commands.add(commands, [lib], depfiles + list(f_files.keys()))
            self.f_files.update(f_files)

        self.edam = edam.copy()
        self.edam["files"] = unused_files

        self.commands = EdaCommands()

        _parameters = []

        db_file = str(Path("work") / "_lib.qdb")
        self.commands.add(
            ["vsim"] + ["-c", "-do", '"do edalize_main.tcl; exit"'],
            [db_file],
            depfiles + ["edalize_main.tcl", "edalize_build_rtl.tcl"],
        )

        for key, value in self.vlogparam.items():
            _parameters += ["-g", "{}={}".format(key, self._param_value_str(value))]
        for key, value in self.generic.items():
            _parameters += [
                "-g",
                "{}={}".format(key, self._param_value_str(value, bool_is_str=True)),
            ]

        self.commands.add(
            ["vsim", "-c"]
            + vsim_options
            + _parameters
            + [
                "$(EXTRA_OPTIONS)",
                "-do",
                '"run -all; quit -code [expr [coverage attribute -name TESTSTATUS -concise] >= 2 ? [coverage attribute -name TESTSTATUS -concise] : 0]; exit"',
                self.toplevel,
            ],
            ["run"],
            [db_file],
        )

        self.commands.add(
            ["vsim", "-gui"]
            + vsim_options
            + _parameters
            + ["$(EXTRA_OPTIONS)", self.toplevel],
            ["run-gui"],
            [db_file],
        )
        self.commands.set_default_target(db_file)

    def write_config_files(self):
        tcl_main = "onerror { quit -code 1; }\ndo edalize_build_rtl.tcl\n"

        for f in self.tcl_files:
            tcl_main += f"do {f}\n"

        self.update_config_file("edalize_main.tcl", tcl_main)

        tcl_build_rtl = "\n".join(self.tcl_build_rtl)

        self.update_config_file("edalize_build_rtl.tcl", tcl_build_rtl)

    def run(self):
        args = ["run"]

        # Set plusargs
        if self.plusarg:
            plusargs = []
            for key, value in self.plusarg.items():
                plusargs += ["+{}={}".format(key, self._param_value_str(value))]
            args.append("EXTRA_OPTIONS=" + " ".join(plusargs))

        return ("make", args, self.work_root)
