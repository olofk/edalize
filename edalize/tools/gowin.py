# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import os.path

from edalize.tools.edatool import Edatool
from edalize.utils import EdaCommands
from functools import partial


class Gowin(Edatool):

    description = "Official development tool for Gowin FPGAs"

    TOOL_OPTIONS = {
        "part": {
            "type": "str",
            "desc": "FPGA part number (e.g. GW2AR-LV18QN88C8/I7)",
        },
        "part_version": {
            "type": "str",
            "desc": "Part version. e.g 'C'",
        },
        "synth": {
            "type": "str",
            "desc": "Synthesis tool. Allowed values are gowin (default) or none.",
        },
        "pnr": {
            "type": "str",
            "desc": "P&R tool. Allowed values are gowin (default) and none (to just run synthesis)",
        },
        "gowin_options": {
            "type": "str",
            "desc": "Additional options for Gowin. See Gowin Software User Guide SUG-100 > set_option",
            "list": True,
        },
    }

    def src_file_filter(self, f):
        def _append_library(f):
            s = ""
            if f.get("logical_name"):
                s += (
                    "\nset_file_prop -lib " + f["logical_name"] + ' "' + f["name"] + '"'
                )
            return s

        def _handle_src(t, f):
            s = "add_file -type " + t
            s += ' "' + f["name"] + '"'
            s += _append_library(f)
            return s

        def _handle_tcl(f):
            return "source " + f["name"]

        file_mapping = {
            "verilogSource": partial(_handle_src, "verilog"),
            "systemVerilogSource": partial(_handle_src, "verilog"),
            "vhdlSource": partial(_handle_src, "VHDL_FILE"),
            "CST": partial(_handle_src, "cst"),
            "SDC": partial(_handle_src, "sdc"),
            "tclSource": partial(_handle_tcl),
        }

        _file_type = f.get("file_type")
        if _file_type in file_mapping:
            return file_mapping[_file_type](f)
        elif _file_type == "user":
            return ""

        return ""

    def setup(self, edam):
        super().setup(edam)

        file_table = []
        unused_files = []
        depfiles = []

        has_vhdl2008 = "vhdlSource-2008" in [x["file_type"] for x in self.files]
        has_systemVerilog = "systemVerilogSource" in [
            x["file_type"] for x in self.files
        ]

        escaped_name = self.name.replace(".", "_")

        if not self.tool_options.get("synth"):
            self.tool_options["synth"] = "gowin"

        if not self.tool_options.get("pnr"):
            self.tool_options["pnr"] = "gowin"

        if not self.tool_options.get("part"):
            raise RuntimeError("FPGA part number must be specified")

        if self.generic:
            raise RuntimeError("Gowin does not support top level generics")

        if self.vlogparam:
            raise RuntimeError("Gowin does not support top level verilog parameters")

        if self.vlogdefine:
            raise RuntimeError("Gowin does not support top level verilog defines")

        commands = EdaCommands()

        for f in self.files:
            cmd = self.src_file_filter(f)

            if cmd:
                depfiles.append(f["name"])
                file_table.append(cmd)
            else:
                unused_files.append(f)

        self.edam = edam.copy()
        self.edam["files"] = unused_files

        fs_file = os.path.join("pnr", escaped_name + ".fs")

        self.edam["files"].append(
            {
                "name": fs_file,
            }
        )

        self.template_vars = {
            "name": escaped_name,
            "file_table": file_table,
            "tool_options": self.tool_options,
            "toplevel": self.toplevel,
            "has_vhdl2008": has_vhdl2008,
            "has_systemVerilog": has_systemVerilog,
        }

        commands.add(
            ["gw_sh", "edalize_gowin_template.tcl"],
            [fs_file],
            depfiles,
        )

        commands.set_default_target(fs_file)
        self.commands = commands

    def write_config_files(self):
        self.render_template(
            "gowin-project.tcl.j2", "edalize_gowin_template.tcl", self.template_vars
        )
