# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import os
import logging

from edalize.tools.edatool import Edatool
from edalize.utils import EdaCommands

logger = logging.getLogger(__name__)


class Modelsim(Edatool):
    description = "ModelSim simulator from Mentor Graphics"

    TOOL_OPTIONS = {
        "compilation_mode": {
            "type": "str",
            "desc": "Common or separate compilation, sep - for separate compilation, common - for common compilation",
        },
        "vcom_options": {
            "type": "str",
            "desc": "Additional options for compilation with vcom",
        },
        "vlog_options": {
            "type": "str",
            "desc": "Additional options for compilation with vlog",
        },
        "vsim_options": {
            "type": "str",
            "desc": "Additional run options for vsim",
        },
        # run_options?
    }

    def _write_build_rtl_tcl_file(self, tcl_main):
        incdirs = []
        libs = []
        vlog_files = []

        tcl_build_rtl = open(os.path.join(self.work_root, "edalize_build_rtl.tcl"), "w")

        # Fill up incdirs with all include directories, before looping through all files.
        for f in self.files:
            self._add_include_dir(f, incdirs)

        vlog_include_dirs = ["+incdir+" + d.replace("\\", "/") for d in incdirs]

        common_compilation = self.tool_options.get("compilation_mode") == "common"

        for f in self.files:
            if not f.get("logical_name"):
                f["logical_name"] = "work"
            if not f["logical_name"] in libs:
                tcl_build_rtl.write("vlib {}\n".format(f["logical_name"]))
                libs.append(f["logical_name"])
            if f["file_type"].startswith("verilogSource") or f["file_type"].startswith(
                "systemVerilogSource"
            ):
                cmd = None

                if not f.get("is_include_file"):
                    # Add vlog command for non-include file types
                    vlog_files.append(f["name"])
                    cmd = "vlog"

                args = []

                args += self.tool_options.get("vlog_options", [])

                for k, v in self.vlogdefine.items():
                    args += ["+define+{}={}".format(k, self._param_value_str(v))]

                if f["file_type"].startswith("systemVerilogSource"):
                    args += ["-sv"]

                args += vlog_include_dirs
            elif f["file_type"].startswith("vhdlSource"):
                cmd = "vcom"
                if f["file_type"].endswith("-87"):
                    args = ["-87"]
                if f["file_type"].endswith("-93"):
                    args = ["-93"]
                if f["file_type"].endswith("-2008"):
                    args = ["-2008"]
                else:
                    args = []

                args += self.tool_options.get("vcom_options", [])

            elif f["file_type"] == "tclSource":
                cmd = None
                tcl_main.write("do {}\n".format(f["name"]))
            elif f["file_type"] == "user":
                cmd = None
            else:
                _s = "{} has unknown file type '{}'"
                logger.warning(_s.format(f["name"], f["file_type"]))
                cmd = None
            if cmd and ((cmd != "vlog") or not common_compilation):
                args += ["-quiet"]
                args += ["-work", f["logical_name"]]
                args += [f["name"].replace("\\", "/")]
                tcl_build_rtl.write("{} {}\n".format(cmd, " ".join(args)))
        if common_compilation:
            args = self.tool_options.get("vlog_options", [])
            for k, v in self.vlogdefine.items():
                args += ["+define+{}={}".format(k, self._param_value_str(v))]

            _vlog_files = []
            has_sv = False
            for f in vlog_files:
                _vlog_files.append(f["name"].replace("\\", "/"))
                if f["file_type"].startswith("systemVerilogSource"):
                    has_sv = True

            if has_sv:
                args += ["-sv"]
            args += vlog_include_dirs
            args += ["-quiet"]
            args += ["-work", "work"]
            args += ["-mfcu"]
            tcl_build_rtl.write(f"vlog {' '.join(args)} {' '.join(_vlog_files)}")

    def write_config_files(self):
        """
        Generate ModelSim specific makefile & TCL build files from template.
        """

        tcl_main = open(os.path.join(self.work_root, "edalize_main.tcl"), "w")
        tcl_main.write("onerror { quit -code 1; }\n")
        tcl_main.write("do edalize_build_rtl.tcl\n")
        self._write_build_rtl_tcl_file(tcl_main)
        tcl_main.close()

        self.render_template(
            "modelsim-makefile.j2",
            "modelsim-makefile",
            self.template_vars,
        )

    def setup(self, edam):
        super().setup(edam)

        depfiles = []

        _parameters = []
        for key, value in self.vlogparam.items():
            _parameters += ["{}={}".format(key, self._param_value_str(value))]
        for key, value in self.generic.items():
            _parameters += [
                "{}={}".format(key, self._param_value_str(value, bool_is_str=True))
            ]
        _plusargs = []
        for key, value in self.plusarg.items():
            _plusargs += ["{}={}".format(key, self._param_value_str(value))]

        _vsim_options = self.tool_options.get("vsim_options", [])
        _modules = [m["name"] for m in self.vpi_modules]
        _clean_targets = " ".join(["clean_" + m for m in _modules])

        self.template_vars = {
            "toplevel": self.toplevel,
            "name": self.name,
            "vsim_options": " ".join(_vsim_options),
            "parameters": " ".join(_parameters),
            "plusargs": " ".join(_plusargs),
            "modules": " ".join(_modules),
        }

        commands = EdaCommands()

        commands.add(
            ["make"]
            + [
                "-f",
                "modelsim-makefile",
                "work",
            ],
            ["modelsim-build"],
            depfiles,
        )

        commands.add(
            ["make"]
            + [
                "-f",
                "modelsim-makefile",
                "run",
            ],
            ["modelsim-run"],
            ["modelsim-build"],
        )

        commands.add(
            ["make"]
            + [
                "-f",
                "modelsim-makefile",
                "run-gui",
            ],
            ["modelsim-run-gui"],
            ["modelsim-build"],
        )

        commands.set_default_target("modelsim-build")
        self.commands = commands

    def run(self):
        args = ["modelsim-run"]

        # Set plusargs
        if self.plusarg:
            plusargs = []
            for key, value in self.plusarg.items():
                plusargs += ["{}={}".format(key, self._param_value_str(value))]
            args.append("PLUSARGS=" + " ".join(plusargs))

        return ("make", args, self.work_root)
