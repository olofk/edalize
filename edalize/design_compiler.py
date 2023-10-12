# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import logging
import os.path
import platform
import re
import subprocess

from edalize.edatool import Edatool
from edalize.utils import get_file_type
from edalize.yosys import Yosys
from importlib import import_module

logger = logging.getLogger(__name__)

""" design-compiler Backend

A core (usually the system core) can add the following files:

- Standard design sources

- Libraries
"""


class Design_compiler(Edatool):

    argtypes = ["vlogdefine", "vlogparam", "generic"]

    @classmethod
    def get_doc(cls, api_ver):
        if api_ver == 0:
            return {
                "description": "The design_compiler backend executes Synopsys design_copiler to build a gate-level netlist",
                "members": [
                    {
                        "name": "script_dir",
                        "type": "String",
                        "desc": "Path to Syopsys scripts (e.g. /home/user/project/synopsys/scripts)",
                    },
                    {
                        "name": "dc_script",
                        "type": "String",
                        "desc": "Name of the synthesis script to run [located in script_dir](e.g. synth.tcl)",
                    },
                    {
                        "name": "report_dir",
                        "type": "String",
                        "desc": "Path to where reports should be stored (e.g. /home/user/project/synopsys/reports)",
                    },
                    {
                        "name": "target_library",
                        "type": "String",
                        "desc": "The Design Compiler target_library",
                    },
                    {
                        "name": "libs",
                        "type": "String",
                        "desc": "Libraries to use in the Design Compiler link_library",
                    },
                    {
                        "name": "jobs",
                        "type": "Integer",
                        "desc": "Number of jobs. Useful for parallelizing syntheses.",
                    },
                ],
            }

    """ Configuration is the first phase of the build
    This writes the project TCL files and Makefile. It first collects all
    sources, IPs and constraints and then writes them to the TCL file along
     with the build steps.
    """

    def configure_main(self):
        def make_list(opt):
            if opt:
                opt = (
                    ((opt.replace("[", "")).replace("]", "")).replace(",", "")
                ).replace("'", "")
            return opt

        (src_files, incdirs) = self._get_fileset_files(force_slash=True)

        self.jinja_env.filters["src_file_filter"] = self.src_file_filter

        self.synth_tool = self.tool_options.get("synth", "design-compiler")

        template_vars = {
            "name": self.name,
            "src_files": src_files,
            "incdirs": incdirs + ["."],
            "tool_options": self.tool_options,
            "script_dir": make_list(self.tool_options.get("script_dir")),
            "dc_script": make_list(self.tool_options.get("dc_script")),
            "report_dir": make_list(self.tool_options.get("report_dir")),
            "target_library": self.tool_options.get("target_library"),
            "libs": make_list(self.tool_options.get("libs")),
            "toplevel": self.toplevel,
        }

        design_compiler_settings = self.tool_options.get(
            "design_compiler-settings", None
        )
        design_compiler_command = (
            "source {} && design_compiler".format(design_compiler_settings)
            if design_compiler_settings
            else "design_compiler"
        )

        self.render_template(
            "design-compiler-makefile.j2",
            "Makefile",
            {
                "name": self.name,
                "report_dir": make_list(self.tool_options.get("report_dir")),
                "design_compiler_command_command": design_compiler_command,
            },
        )

        jobs = self.tool_options.get("jobs", None)

        run_template_vars = {"jobs": " -jobs " + str(jobs) if jobs is not None else ""}

        self.render_template(
            "design-compiler-project.tcl.j2", self.name + ".tcl", template_vars
        )

        self.render_template(
            "design-compiler-read-sources.tcl.j2",
            self.name + "-read-sources.tcl",
            template_vars,
        )

    def src_file_filter(self, f):
        file_types = {
            "verilogSource": "analyze -format verilog",
            "systemVerilogSource": "analyze -format sverilog",
            "vhdlSource": "analyze -format vhdl",
            "tclSource": "source",
            "SDC": "source",
        }

        _file_type = get_file_type(f)
        if _file_type in file_types:
            cmd = ""
            cmd += file_types[_file_type] + " "

            if (_file_type != "tclSource") and (_file_type != "SDC"):
                cmd_define = ""
                if (_file_type != "vhdlSource") and (self.vlogdefine.items() != {}):
                    cmd_define = "-define {"
                    for k, v in self.vlogdefine.items():
                        # Skip reddefinition of SYNTHESIS which is a reserved macro in IEEE Verilog synthesizable subset
                        if k != "SYNTHESIS":
                            cmd_define += " {}={}".format(k, self._param_value_str(v))
                    cmd_define += " }"

                cmd += cmd_define + " " + "-work work " + f.name
            else:
                cmd += " " + f.name

            return cmd

        if _file_type == "user":
            return ""

        _s = "{} has unknown file type '{}', interpretation is up to Design Compiler"
        logger.warning(_s.format(f.name, f.file_type))
        return "add_files -norecurse" + " " + f.name

    def build_main(self):
        logger.info("Building")
        logger.info(
            "(running make, which runs dc_shell which has an unbelievably long lag before printing. be patient)"
        )
        args = []
        self._run_tool("make", args, quiet=True)
