# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

from io import StringIO
import os

from edalize.tools.edatool import Edatool
from edalize.utils import EdaCommands


class Modelsim(Edatool):

    description = "Modelsim is a simulation tool."

    TOOL_OPTIONS = {
        "vsim_options": {
            "type": "str",
            "desc": "Additional options for iverilog",
        },
        "vlog_options": {
            "type": "str",
            "desc": "Additional options for vvp",
        },
        "vcom_options": {
            "type": "str",
            "desc": "Additional options for vvp",
        },
    }

    def setup(self, edam):
        super().setup(edam)

        build_file = StringIO()
        incdirs = []
        vlog_files = []
        depfiles = []
        unused_files = []
        libs = []

        vlog_include_dirs = ["+incdir+" + d.replace("\\", "/") for d in incdirs]

        for f in self.files:
            file_type = f.get("file_type", "")
            logical_name = f.get("logical_name", "work")
            depfile = True

            if not logical_name in libs:
                build_file.write("vlib {}\n".format(logical_name))
                libs.append(logical_name)
            if file_type.startswith("verilogSource") or file_type.startswith("systemVerilogSource"):
                if not self._add_include_dir(f, incdirs):
                    vlog_files.append(f["name"])

                cmd = "vlog"
                args = []

                args += self.tool_options.get("vlog_options", [])

                for k, v in self.vlogdefine.items():
                    args += ["+define+{}={}".format(k, self._param_value_str(v))]

                if file_type.startswith("systemVerilogSource"):
                    args += ["-sv"]
                args += vlog_include_dirs
            elif file_type.startswith("vhdlSource"):
                cmd = "vcom"
                if file_type.endswith("-87"):
                    args = ["-87"]
                if file_type.endswith("-93"):
                    args = ["-93"]
                if file_type.endswith("-2008"):
                    args = ["-2008"]
                else:
                    args = []

                args += self.tool_options.get("vcom_options", [])
            elif file_type == "tclSource":
                cmd = None
                build_file.write("do {}\n".format(f["name"]))
            else:
                unused_files.append(f)
                depfile = False
                cmd = None

            if depfile:
                depfiles.append(f["name"])

            if cmd:
                args += ["-quiet"]
                args += ["-work", logical_name]
                args += [f["name"].replace("\\", "/")]
                build_file.write("{} {}\n".format(cmd, " ".join(args)))

        for include_dir in incdirs:
            build_file.write(f"+incdir+{include_dir}\n")

        self.build_file = build_file

        self.edam = edam.copy()
        self.edam["files"] = unused_files

        commands = EdaCommands()
        commands.add(["vsim","-c","-do",f"build_{self.name}.do"],
                     [self.name],
                     depfiles + [f"build_{self.name}.do"])
        
        libsargs = ["-L " + l for l in libs]
        plusargs = []
        for key, value in self.plusarg.items():
            plusargs += ["+{}={}".format(key, self._param_value_str(value))]

        run_command = ["vsim", "-c"]
        run_command.extend(libsargs)
        run_command.extend(self.tool_options.get("vsim_options",""))
        run_command.append(self.toplevel)
        run_command.extend(plusargs if plusargs else "")
        run_command.append('-do "run -all; quit"')

        commands.add(run_command,
                     ["run"],
                     [self.name])

        commands.set_default_target(self.name)
        self.commands = commands

    def write_config_files(self):
        self.update_config_file(f"build_{self.name}.do", self.build_file.getvalue())

    def run(self):
        return ("make", ["run"], self.work_root)
