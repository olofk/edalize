# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import logging
import re
from collections import OrderedDict

from edalize.edatool import Edatool

logger = logging.getLogger(__name__)


class Dc_shell(Edatool):

    _description = """ Synopsys (formerly Atrenta) DC_shell Backend

This module generates the file list for dc_shell. 
"""

    tool_options = {
        "lists": {
            "dc_options": "String",
        },
    }

    argtypes = ["vlogdefine", "vlogparam"]

    tool_options_defaults = {
        "dc_options": [],
    }

    def _set_tool_options_defaults(self):
        for key, default_value in self.tool_options_defaults.items():
            if not key in self.tool_options:
                logger.info(
                    "Set Spyglass tool option %s to default value %s"
                    % (key, str(default_value))
                )
                self.tool_options[key] = default_value

    def configure_main(self):
        """
        Configuration is the first phase of the build.

        This writes the project TCL files and Makefile. It first collects all
        sources, IPs and constraints and then writes them to the TCL file along
        with the build steps.
        """
        self._set_tool_options_defaults()

        (src_files, incdirs) = self._get_fileset_files(force_slash=True)

        self.jinja_env.filters["src_file_filter"] = self.src_file_filter

        has_systemVerilog = False
        for src_file in src_files:
            if src_file.file_type.startswith("systemVerilogSource"):
                has_systemVerilog = True
                break

        # Spyglass expects all parameters in the form module.parameter
        # Always prepend the toplevel module name to be consistent with all other
        # backends, which do not require this syntax.
        vlogparam_spyglass = OrderedDict(
            (self.toplevel + "." + p, v) for (p, v) in self.vlogparam.items()
        )

        template_vars = {
            "name": self.name,
            "src_files": src_files,
            "incdirs": incdirs,
            "tool_options": self.tool_options,
            "toplevel": self.toplevel,
            "vlogparam": vlogparam_spyglass,
            "vlogdefine": self.vlogdefine,
            "has_systemVerilog": has_systemVerilog,
            "sanitized_goals": [],
        }

        self.render_template(
            "dc_shell.tcl.j2", self.name + ".tcl", template_vars
        )

    def src_file_filter(self, f):

        file_types = {
            "verilogSource": "analyze -format sverilog",
            "systemVerilogSource": "analyze -format sverilog",
        }
        _file_type = f.file_type.split("-")[0]
        if _file_type in file_types:
            return file_types[_file_type] + " " + f.name
        elif _file_type == "user":
            return ""
        else:
            _s = "{} has unknown file type '{}'"
            logger.warning(_s.format(f.name, f.file_type))
        return ""

    def run_main(self):
        args = ["-i"]

        # Set plusargs
        if self.plusarg:
            plusargs = []
            for key, value in self.plusarg.items():
                plusargs += ["+{}={}".format(key, self._param_value_str(value))]
            args.append("EXTRA_OPTIONS=" + " ".join(plusargs))

        self._run_tool("make", args)
