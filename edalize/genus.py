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

""" Cadence Genus Backend

A core (usually the system core) can add the following files:

- Standard design sources

- Libraries
"""


class Genus(Edatool):

    argtypes = ["vlogdefine", "vlogparam", "generic"]

    @classmethod
    def get_doc(cls, api_ver):
        if api_ver == 0:
            return {
                "description": "The genus backend executes cadence genus to build a gate-level netlist",
                "members": [
                    {
                        "name": "script_dir",
                        "type": "String",
                        "desc": "Path to Genus scripts (e.g. /home/user/project/genus/scripts)",
                    },
                    {
                        "name": "genus_script",
                        "type": "String",
                        "desc": "Name of the synthesis script to run [located in script_dir](e.g. synth.tcl)",
                    },
                    {
                        "name": "report_dir",
                        "type": "String",
                        "desc": "Path to where reports should be stored (e.g. /home/user/project/genus/reports)",
                    },
                    {
                        "name": "common_config",
                        "type": "String",
                        "desc": "A TCL file to be sourced, defining common project specific variables shared between genus and innovus (Loction of MMMC view, LEFs, DEFs, UPF, Paths, ...)",
                    },
                    {
                        "name": "jobs",
                        "type": "String",
                        "desc": 'Number of jobs. Useful for parallelizing syntheses. Use "all" to set the number of jobs to the number of cores available.',
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

        self.synth_tool = self.tool_options.get("synth", "genus")

        jobs = self.tool_options.get("jobs", None)
        jobs = "$nproc" if "all" in jobs else jobs

        template_vars = {
            "name": self.name,
            "src_files": src_files,
            "incdirs": incdirs + ["."],
            "tool_options": self.tool_options,
            "script_dir": make_list(self.tool_options.get("script_dir")),
            "genus_script": make_list(self.tool_options.get("genus_script")),
            "report_dir": make_list(self.tool_options.get("report_dir")),
            "common_config": make_list(self.tool_options.get("common_config")),
            "jobs": make_list(jobs),
            "toplevel": self.toplevel,
        }

        genus_settings = self.tool_options.get("genus-settings", None)
        genus_command = (
            "source {} && genus".format(genus_settings) if genus_settings else "genus"
        )

        self.render_template(
            "genus-makefile.j2",
            "Makefile",
            {
                "name": self.name,
                "report_dir": make_list(self.tool_options.get("report_dir")),
                "genus_command_command": genus_command,
            },
        )

        self.render_template("genus-project.tcl.j2", self.name + ".tcl", template_vars)

        self.render_template(
            "genus-read-sources.tcl.j2", self.name + "-read-sources.tcl", template_vars
        )

    def src_file_filter(self, f):
        file_types = {
            "verilogSource": "read_hdl -language v2001",
            "systemVerilogSource": "read_hdl -language sv",
            "vhdlSource": "read_hdl -language vhdl",
            "tclSource": "source",
            # Note: we do not add an SDC source here as the constraint files are
            # referenced inside the MMMC view file on a per corner base
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

                cmd += cmd_define + " " + "-library work " + f.name
            else:
                cmd += " " + f.name

            return cmd

        if _file_type in file_types:
            return file_types[_file_type] + " " + f.name

        if _file_type == "user":
            return ""

        _s = "{} has unknown file type '{}', interpretation is up to Genus"
        logger.warning(_s.format(f.name, f.file_type))
        return "add_files -norecurse" + " " + f.name

    def build_main(self):
        logger.info("Building")
        logger.info(
            "(running make, which runs genus which has an unbelievably long lag before printing. be patient)"
        )
        args = []
        self._run_tool("make", args, quiet=True)
