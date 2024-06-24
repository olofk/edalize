# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import logging
import os
import xml.etree.ElementTree as ET
from functools import partial
from edalize.edatool import Edatool
from edalize.utils import get_file_type

logger = logging.getLogger(__name__)


class Gowin(Edatool):
    argtypes = ["vlogdefine", "vlogparam", "generic"]

    makefile_template = "gowin-makefile.j2"

    @classmethod
    def get_doc(cls, api_ver):
        if api_ver == 0:
            return {
                "description": "The Gowin backend supports building and programming the FPGA",
                "members": [
                    {
                        "name": "device",
                        "type": "String",
                        "desc": "FPGA device (e.g. GW2AR-LV18QN88C8/I7)",
                    },
                    {
                        "name": "device_version",
                        "type": "String",
                        "desc": "Device version. e.g 'C'",
                    },
                    {
                        "name": "pgm",
                        "type": "String",
                        "desc": "Programming tool. Default is 'none', set to 'openFPGALoader', or 'gowin' to program the FPGA in the run stage.",
                    }
                ],
                "lists": [
                    {
                        "name": "gowin_options",
                        "type": "String",
                        "desc": "Additional options for gowin",
                    }
                ],
                
            }

    def __init__(self, edam=None, work_root=None, eda_api=None, verbose=False):
        """
        Initial setup of the class.

        This calls the parent constructor.
        """
        if not edam:
            edam = eda_api

        super(Gowin, self).__init__(edam, work_root, eda_api, verbose)

    def configure_main(self):
        """
        Configuration is the first phase of the build.

        This writes the project TCL files and Makefile. It first collects all
        sources, IPs and constraints and then writes them to the TCL file along
        with the build steps.
        """
        (src_files, incdirs) = self._get_fileset_files(force_slash=True)
        self.jinja_env.filters["src_file_filter"] = self.src_file_filter

        has_vhdl2008 = "vhdlSource-2008" in [x.file_type for x in src_files]

        escaped_name = self.name.replace(".", "_")

        template_vars = {
            "name": escaped_name,
            "src_files": src_files,
            "incdirs": incdirs,
            "tool_options": self.tool_options,
            "toplevel": self.toplevel,
            "vlogparam": self.vlogparam,
            "vlogdefine": self.vlogdefine,
            "generic": self.generic,
            "has_vhdl2008": has_vhdl2008,
        }

        # Render Makefile based on detected version
        self.render_template(
            self.makefile_template,
            "Makefile",
            {
                "name": escaped_name,
                "src_files": src_files,
                "tool_options": self.tool_options,
            },
        )

        # Render the TCL project file
        self.render_template(
            "gowin-project.tcl.j2", escaped_name + ".tcl", template_vars
        )

    # Allow the templates to get source file information
    def src_file_filter(self, f):
        def _append_library(f):
            s = ""
            if f.logical_name:
                s += " -library " + f.logical_name
            return s

        def _handle_src(t, f):
            s = "add_file -type " + t
            s += _append_library(f)
            s += " \"" + f.name + "\""
            return s

        def _handle_tcl(f):
            return "source " + f.name

        file_mapping = {
            "verilogSource": partial(_handle_src, "verilog"),
            "systemVerilogSource": partial(_handle_src, "verilog"),
            "vhdlSource": partial(_handle_src, "VHDL_FILE"),
            "CST": partial(_handle_src, "cst"),
            "SDC": partial(_handle_src, "sdc"),
            "tclSource": partial(_handle_tcl),
        }

        _file_type = get_file_type(f)
        if _file_type in file_mapping:
            return file_mapping[_file_type](f)
        elif _file_type == "user":
            return ""
        else:
            _s = "{} has unknown file type '{}'"
            logger.warning(_s.format(f.name, f.file_type))

        return ""

    def build_main(self):
        logger.info("Building")
        args = []
        self._run_tool("make", args, quiet=True)

    def run_main(self):
        """
        Program the FPGA.
        """


        print(self.tool_options)

        if "pgm" not in self.tool_options:
            return
        
        if isinstance(self.tool_options["pgm"], list):
            self.tool_options["pgm"] = self.tool_options["pgm"][0]

        if self.tool_options["pgm"] == 'gowin':
            args = ["--device", self.tool_options["device"]]
            if "cable" in self.tool_options:
                args += ["--cable", self.tool_options["cable"]]
            args += ["--fsFile", "impl/pnr/project.fs"]
            self._run_tool("ls", [])
        elif self.tool_options["pgm"] == 'openFPGALoader':
            args = ["--bitstream", "impl/pnr/project.fs"]
            self._run_tool("openFPGALoader", args)

        
