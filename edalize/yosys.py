# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import logging
import os.path

from edalize.edatool import Edatool
from edalize.utils import EdaCommands

logger = logging.getLogger(__name__)


class Yosys(Edatool):

    argtypes = ["vlogdefine", "vlogparam"]

    @classmethod
    def get_doc(cls, api_ver):
        if api_ver == 0:
            return {
                "description": "Open source synthesis tool targeting many different FPGAs",
                "members": [
                    {
                        "name": "arch",
                        "type": "String",
                        "desc": "Target architecture. Legal values are *xilinx*, *ice40* and *ecp5*",
                    },
                    {
                        "name": "output_format",
                        "type": "String",
                        "desc": "Output file format. Legal values are *json*, *edif*, *blif*, *verilog*",
                    },
                    {
                        "name": "output_name",
                        "type": "String",
                        "desc": "Output file name. [Optional]",
                    },
                    {
                        "name": "yosys_as_subtool",
                        "type": "bool",
                        "desc": "Determines if Yosys is run as a part of bigger toolchain, or as a standalone tool",
                    },
                    {
                        "name": "makefile_name",
                        "type": "String",
                        "desc": "Generated makefile name, defaults to $name.mk",
                    },
                    {
                        "name": "yosys_template",
                        "type": "String",
                        "desc": "TCL template file to use instead of default template",
                    },
                ],
                "lists": [
                    {
                        "name": "yosys_synth_options",
                        "type": "String",
                        "desc": "Additional options for the synth command",
                    },
                ],
            }

    def configure_main(self):
        # write Yosys tcl script file

        yosys_template = self.tool_options.get("yosys_template")

        incdirs = []
        file_table = []
        unused_files = []

        for f in self.files:
            cmd = ""
            if f["file_type"].startswith("verilogSource"):
                cmd = "read_verilog"
            elif f["file_type"].startswith("systemVerilogSource"):
                cmd = "read_verilog -sv"
            elif f["file_type"] == "tclSource":
                cmd = "source"

            if cmd:
                if not self._add_include_dir(f, incdirs):
                    file_table.append(cmd + " {" + f["name"] + "}")
            else:
                unused_files.append(f)

        self.edam["files"] = unused_files

        output_format = self.tool_options.get("output_format", "blif")
        default_target = self.tool_options.get(
            "output_name", f"{self.name}.{output_format}"
        )

        self.edam["files"].append(
            {
                "name": default_target,
                "file_type": "jsonNetlist"
                if output_format == "json"
                else output_format,
            }
        )

        verilog_defines = []
        for key, value in self.vlogdefine.items():
            verilog_defines.append("{{{key} {value}}}".format(key=key, value=value))

        verilog_params = []
        for key, value in self.vlogparam.items():
            if type(value) is str:
                value = '{"' + value + '"}'
            _s = r"chparam -set {} {} {}"
            verilog_params.append(
                _s.format(key, self._param_value_str(value), self.toplevel)
            )

        arch = self.tool_options.get("arch", None)

        if not arch:
            logger.error("ERROR: arch is not defined.")

        template = yosys_template or "edalize_yosys_template.tcl"
        template_vars = {
            "verilog_defines": "{" + " ".join(verilog_defines) + "}",
            "verilog_params": "\n".join(verilog_params),
            "file_table": "\n".join(file_table),
            "incdirs": " ".join(["-I" + d for d in incdirs]),
            "top": self.toplevel,
            "synth_command": "synth_" + arch,
            "synth_options": " ".join(self.tool_options.get("yosys_synth_options", "")),
            "write_command": "write_" + output_format,
            "output_name": default_target,
            "output_opts": "-pvector bra "
            if (arch == "xilinx" and output_format == "edif")
            else "",
            "yosys_template": template,
            "name": self.name,
        }

        self.render_template(
            "edalize_yosys_procs.tcl.j2", "edalize_yosys_procs.tcl", template_vars
        )

        if not yosys_template:
            self.render_template(
                "yosys-script-tcl.j2", "edalize_yosys_template.tcl", template_vars
            )

        commands = EdaCommands()
        commands.add(
            ["yosys", "-l", "yosys.log", "-p", f"'tcl {template}'"],
            [default_target],
            [template],
        )
        if self.tool_options.get("yosys_as_subtool"):
            self.commands = commands.commands
        else:
            commands.set_default_target(default_target)
            commands.write(os.path.join(self.work_root, "Makefile"))
