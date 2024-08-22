# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

from pathlib import Path

from edalize.tools.edatool import Edatool
from edalize.utils import EdaCommands


class Modelsim(Edatool):

    description = "ModelSim/QuestaSim simulator from Siemens EDA"

    TOOL_OPTIONS = {
        "compilation_mode": {
            "type": "str",
            "desc": "Common or separate compilation, sep - for separate compilation, common - for common compilation",
        },
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
        vlog_files = []
        depfiles = []
        unused_files = []
        libs = []

        vlog_defines = []
        for k, v in self.vlogdefine.items():
            vlog_defines.append("+define+{}={}".format(k, self._param_value_str(v)))

        common_compilation = self.tool_options.get("compilation_mode") == "common"
        vlog_options = self.tool_options.get("vlog_options", [])
        vcom_options = self.tool_options.get("vcom_options", [])
        vsim_options = self.tool_options.get("vsim_options", [])

        # Get all include dirs first
        for f in self.files:
            file_type = f.get("file_type", "")
            if file_type.startswith("verilogSource") or file_type.startswith(
                "systemVerilogSource"
            ):
                self._add_include_dir(f, incdirs, force_slash=True)

        vlog_include_dirs = ["+incdir+" + d.replace("\\", "/") for d in incdirs]

        self.tcl_files = []
        self.tcl_main = []
        self.tcl_build_rtl = []
        for f in self.files:
            if not f.get("logical_name"):
                f["logical_name"] = "work"
            if not f["logical_name"] in libs:
                self.tcl_build_rtl.append(f"vlib {f['logical_name']}")
                libs.append(f["logical_name"])
            file_type = f.get("file_type", "")
            if file_type.startswith("verilogSource") or file_type.startswith(
                "systemVerilogSource"
            ):
                depfiles.append(f["name"])
                if self._add_include_dir(f, incdirs, force_slash=True):
                    cmd = None
                else:
                    vlog_files.append(f)
                    cmd = "vlog"
                args = []

                args += vlog_include_dirs
                args += vlog_options
                args += vlog_defines

                if file_type.startswith("systemVerilogSource"):
                    args += ["-sv"]

            elif file_type.startswith("vhdlSource"):
                depfiles.append(f["name"])
                cmd = "vcom"
                if file_type.endswith("-87"):
                    args = ["-87"]
                if file_type.endswith("-93"):
                    args = ["-93"]
                if file_type.endswith("-2008"):
                    args = ["-2008"]
                else:
                    args = []

                args += vcom_options

            elif file_type == "tclSource":
                depfiles.append(f["name"])
                cmd = None
                self.tcl_files.append(f["name"])
            elif file_type == "user":
                depfiles.append(f["name"])
                cmd = None
            else:
                unused_files.append(f)
                cmd = None
            if cmd and ((cmd != "vlog") or not common_compilation):
                args += ["-quiet"]
                args += ["-work", f["logical_name"]]
                args += [f["name"].replace("\\", "/")]
                self.tcl_build_rtl.append(f"{cmd} {' '.join(args)}")

        if common_compilation:
            args = vlog_include_dirs + vlog_options + vlog_defines
            _vlog_files = []
            has_sv = False
            for f in vlog_files:
                _vlog_files.append(f["name"].replace("\\", "/"))
                if f.get("file_type", "").startswith("systemVerilogSource"):
                    has_sv = True

            if has_sv:
                args += ["-sv"]
            args += vlog_include_dirs
            args += ["-quiet"]
            args += ["-work", "work"]
            args += ["-mfcu"]
            self.tcl_build_rtl.append(f"vlog {' '.join(args)} {' '.join(_vlog_files)}")

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
