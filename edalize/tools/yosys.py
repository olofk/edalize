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
            "desc": "Output file format. Legal values are *json*, *edif*, *blif*, *verilog*",
        },
        "yosys_template": {
            "type": "str",
            "desc": "TCL template file to use instead of default template",
        },
        "f4pga_synth_part_file": {
            "type": "str",
            "desc": "The JSON part file used for Yosys synthesis",
        },
        "yosys_synth_options": {
            "type": "str",
            "desc": "Additional options for the synth command",
            "list": True,
        },
    }

    def setup(self, edam):
        super().setup(edam)

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

            if "simulation" in f.get("tags", []):
                cmd = ""

            if cmd:
                depfiles.append(f["name"])
                if not self._add_include_dir(f, incdirs):
                    file_table.append(cmd + " {" + f["name"] + "}")
            else:
                unused_files.append(f)

        self.edam = edam.copy()
        self.edam["files"] = unused_files

        output_format = self.tool_options.get("output_format", "blif")
        default_target = (
            f"{self.name}.{'v' if output_format == 'verilog' else output_format}"
        )

        self.edam["files"].append(
            {
                "name": default_target,
                "file_type": "jsonNetlist"
                if output_format == "json"
                else "verilogSource"
                if output_format == "verilog"
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

        arch = self._require_tool_option("arch")

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
            "output_format": "v" if output_format == "verilog" else output_format,
            "output_opts": "-pvector bra "
            if (arch == "xilinx" and output_format == "edif")
            else "",
            "yosys_template": template,
            "name": self.name,
        }
        self.template_vars = template_vars

        commands = EdaCommands()

        # First, check if split_io list is passed in and is the correct size
        f4pga_synth_part_file = ""
        if "f4pga_synth_part_file" in self.tool_options:
            f4pga_synth_part_file = self.tool_options.get("f4pga_synth_part_file")

        # Configure first call to Yosys
        targets = []
        depends = depfiles
        variables = []
        logfile = ""

        targets = [default_target]
        if f4pga_synth_part_file:
            in_xdc = ""
            for f in self.files:
                if f.get("file_type") == "xdc":
                    in_xdc = f["name"]
            if not in_xdc:
                print(
                    "F4PGA flow warning: no Xilinx Design Constraint file (.xdc) specified"
                )
            variables = {
                "USE_ROI": "FALSE",
                "TECHMAP_PATH": "${F4PGA_SHARE_DIR}/techmaps/xc7_vpr/techmap",
                "TOP": self.toplevel,
                "INPUT_XDC_FILES": in_xdc,
                "PART_JSON": f4pga_synth_part_file,
                "OUT_FASM_EXTRA": f"{self.name}_fasm_extra.fasm",
                "OUT_SDC": f"{self.name}.sdc",
                "OUT_SYNTH_V": f"{self.name}_synth.v",
                "PYTHON3": "$(shell which python3)",
                "UTILS_PATH": "${F4PGA_SHARE_DIR}/scripts",
                "OUT_JSON": f"{self.name}.json",
                "SYNTH_JSON": f"{self.name}_io.json",
                "OUT_EBLIF": default_target,
            }
            logfile = f"{self.name}_synth.log"
        else:
            depends = [template] + depends
            logfile = "yosys.log"

        command = ["yosys", f"-l {logfile}", f"-p 'tcl {template}'"]

        if f4pga_synth_part_file:
            command += depfiles

        commands.add(command, targets, depends, variables=variables)
        commands.set_default_target(targets[0])
        self.commands = commands

    def write_config_files(self):
        yosys_template = self.tool_options.get("yosys_template")
        self.render_template(
            "edalize_yosys_procs.tcl.j2",
            "edalize_yosys_procs.tcl",
            self.template_vars,
        )

        if not yosys_template:
            self.render_template(
                "yosys-script-tcl.j2", "edalize_yosys_template.tcl", self.template_vars
            )
