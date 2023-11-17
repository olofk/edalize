# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

from io import StringIO
import os

from edalize.tools.edatool import Edatool
from edalize.utils import EdaCommands


class Icarus(Edatool):

    description = "Icarus Verilog is a Verilog simulation and synthesis tool. It operates as a compiler, compiling source code written in Verilog (IEEE-1364) into some target format"

    TOOL_OPTIONS = {
        "timescale": {
            "type": "str",
            "desc": "Default timescale",
        },
        "iverilog_options": {
            "type": "str",
            "desc": "Additional options for iverilog",
        },
        "vvp_options": {
            "type": "str",
            "desc": "Additional options for vvp",
        },
    }

    def setup(self, edam):
        super().setup(edam)

        scr_file = StringIO()
        incdirs = []
        vlog_files = []
        depfiles = []
        unused_files = []

        if True:

            for key, value in self.vlogdefine.items():
                scr_file.write(
                    "+define+{}={}\n".format(key, self._param_value_str(value, ""))
                )

            for key, value in self.vlogparam.items():
                # We currently have no way to express for which toplevel these parameters should be applied, so apply for all of them and accept the warnings.
                for toplevel in self.toplevel.split(" "):
                    scr_file.write(
                        "+parameter+{}.{}={}\n".format(
                            toplevel, key, self._param_value_str(value, '"')
                        )
                    )

            for id in incdirs:
                scr_file.write("+incdir+" + id + "\n")

            timescale = self.tool_options.get("timescale")
            if timescale:
                with open(os.path.join(self.work_root, "timescale.v"), "w") as tsfile:
                    tsfile.write("`timescale {}\n".format(timescale))
                scr_file.write("timescale.v\n")

            for f in self.files:
                file_type = f.get("file_type", "")
                depfile = True
                if file_type.startswith("systemVerilogSource") or file_type.startswith(
                    "verilogSource"
                ):
                    if not self._add_include_dir(f, incdirs):
                        vlog_files.append(f["name"])
                else:
                    unused_files.append(f)
                    depfile = False

                if depfile:
                    depfiles.append(f["name"])

            for include_dir in incdirs:
                scr_file.write(f"+incdir+{include_dir}\n")

            for vlog_file in vlog_files:
                scr_file.write(f"{vlog_file}\n")

        self.edam = edam.copy()
        self.edam["files"] = unused_files

        commands = EdaCommands()
        commands.add(
            ["iverilog"]
            + [f"-s{t}" for t in self.toplevel.split(" ")]
            + [
                "-c",
                f"{self.name}.scr",
                "-o",
                self.name,
            ]
            + self.tool_options.get("iverilog_options", []),
            [self.name],
            depfiles + [f"{self.name}.scr"],
        )

        # How should the run target be handled?
        # Add VPI support
        commands.add(
            ["vvp", "-n", "-M."]
            + self.tool_options.get("vvp_options", [])
            + [self.name, "-fst", "$(EXTRA_OPTIONS)"],
            ["run"],
            [self.name],
        )

        commands.set_default_target(self.name)
        self.commands = commands
        self.scr_file = scr_file

    def write_config_files(self):
        self.update_config_file(self.name + ".scr", self.scr_file.getvalue())

    def run(self):
        args = ["run"]

        # Set plusargs
        if self.plusarg:
            plusargs = []
            for key, value in self.plusarg.items():
                plusargs += ["+{}={}".format(key, self._param_value_str(value))]
            args.append("EXTRA_OPTIONS=" + " ".join(plusargs))

        return ("make", args, self.work_root)
