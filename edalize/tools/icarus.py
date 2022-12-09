# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import os

from edalize.tools.edatool import Edatool
from edalize.utils import EdaCommands

MAKEFILE_TEMPLATE = """
all: $(VPI_MODULES) $(TARGET)

run: $(VPI_MODULES) $(TARGET)
	vvp -n -M. -l icarus.log $(patsubst %.vpi,-m%,$(VPI_MODULES)) $(TARGET) -fst $(EXTRA_OPTIONS)

clean:
	$(RM) $(VPI_MODULES) $(TARGET)
"""

VPI_MAKE_SECTION = """
{name}_LIBS := {libs}
{name}_INCS := {incs}
{name}_SRCS := {srcs}

{name}.vpi: $({name}_SRCS)
	iverilog-vpi --name={name} $({name}_LIBS) $({name}_INCS) $?

clean_{name}:
	$(RM) {name}.vpi
"""


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
    }

    def configure(self, edam):
        super().configure(edam)

        incdirs = []
        vlog_files = []
        depfiles = []
        unused_files = []

        with open(os.path.join(self.work_root, self.name + ".scr"), "w") as scr_file:

            for key, value in self.vlogdefine.items():
                scr_file.write(
                    "+define+{}={}\n".format(key, self._param_value_str(value, ""))
                )

            for key, value in self.vlogparam.items():
                scr_file.write(
                    "+parameter+{}.{}={}\n".format(
                        self.toplevel, key, self._param_value_str(value, '"')
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
            [
                "iverilog",
                f"-s{self.toplevel}",
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
            ["vvp", "-n", "-M.", self.name, "-fst", "$(EXTRA_OPTIONS)"],
            ["run"],
            [self.name],
        )

        self.default_target = self.name
        self.commands = commands.commands

    def run(self, args):
        args = ["run"]

        # Set plusargs
        if self.plusarg:
            plusargs = []
            for key, value in self.plusarg.items():
                plusargs += ["+{}={}".format(key, self._param_value_str(value))]
            args.append("EXTRA_OPTIONS=" + " ".join(plusargs))

        return ("make", args, self.work_root)
