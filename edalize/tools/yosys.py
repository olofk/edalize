# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import logging
import os.path

from edalize.tools.edatool import Edatool
from edalize.utils import EdaCommands

logger = logging.getLogger(__name__)


class Yosys(Edatool):

    description = "Open source synthesis tool targeting many different FPGAs"

    TOOL_OPTIONS = {
        "arch": {
            "type": "str",
            "desc": "Target architecture. Legal values are *xilinx*, *ice40* and *ecp5*",
        },
        "output_format": {
            "type": "str",
            "desc": "Output file format. Legal values are *json*, *edif*, *blif*",
        },
        "yosys_template": {
            "type": "str",
            "desc": "TCL template file to use instead of default template",
        },
        "split_io": {
            "type": "list",
            "desc": "A list to be used for inserting a python command and extra yosys script",
        },
        "yosys_synth_options": {
            "type": "str",
            "desc": "Additional options for the synth command",
            "list": True,
        },
    }

    def write_config_files(self, edam):
        # write Yosys tcl script file
        yosys_template = self.tool_options.get("yosys_template")

        incdirs = []
        file_table = []
        unused_files = []

        depfiles = []
        has_uhdm = False
        for f in self.files:
            file_type = f.get("file_type", "")
            cmd = ""
            if file_type.startswith("verilogSource"):
                cmd = "read_verilog"
            elif file_type.startswith("systemVerilogSource"):
                cmd = "read_verilog -sv"
            elif file_type == "uhdm":
                cmd = "read_uhdm"
                has_uhdm = True
            elif file_type == "tclSource":
                cmd = "source"

            if cmd:
                depfiles.append(f["name"])
                if not self._add_include_dir(f, incdirs):
                    file_table.append(cmd + " {" + f["name"] + "}")
            else:
                unused_files.append(f)

        self.edam = edam.copy()
        self.edam["files"] = unused_files

        output_format = self.tool_options.get("output_format", "blif")
        default_target = f"{self.name}.{output_format}"

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

        arch = self.tool_options.get("arch")

        if not arch:
            logger.error("ERROR: arch is not defined.")

        plugins = []
        if has_uhdm:
            plugins.append("uhdm")

        template = yosys_template or "edalize_yosys_template.tcl"
        template_vars = {
            "plugins": "\n".join("plugin -i " + p for p in plugins),
            "verilog_defines": "{" + " ".join(verilog_defines) + "}",
            "verilog_params": "\n".join(verilog_params),
            "file_table": "\n".join(file_table),
            "incdirs": " ".join(["-I" + d for d in incdirs]),
            "top": self.toplevel,
            "synth_command": "synth_" + arch,
            "synth_options": " ".join(self.tool_options.get("yosys_synth_options", "")),
            "write_command": "write_" + output_format,
            "output_format": output_format,
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

        # First, check if split_io list is passed in and is the correct size
        split_io_list = []
        if (
            self.tool_options.get("split_io")
            and len(self.tool_options.get("split_io")) == 8
        ):
            split_io_list = self.tool_options.get("split_io")

        # Configure first call to Yosys
        targets = []
        depends = []
        args = ""
        variables = []

        if split_io_list:
            targets = f"{self.name}.json"
            depends += depfiles
            args = split_io_list[0]
            variables = split_io_list[2]
        else:
            targets = [default_target]
            depends = [template] + depfiles
            args = f"-p 'tcl {template}'"

        command = ["yosys", "-l yosys.log", args]
        commands.add(command, targets, depends, variables=variables)

        # Configure python script and additional call to Yosys
        if split_io_list:
            targets = f"{self.name}_io.json"
            depends = f"{self.name}.json"
            command = [
                "python3",
                "-m f4pga.utils.split_inouts",
                f"-i {self.name}.json",
                f"-o {self.name}_io.json",
            ]
            commands.add(command, [targets], [depends])

            targets = default_target
            depends = f"{self.name}_io.json"
            command = ["yosys", split_io_list[1]]
            commands.add(command, [targets], [depends], variables=split_io_list[3])

        self.commands = commands.commands
