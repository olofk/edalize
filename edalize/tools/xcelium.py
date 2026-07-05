# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import logging

from edalize.tools.edatool import Edatool
from edalize.utils import EdaCommands

logger = logging.getLogger(__name__)


class Xcelium(Edatool):
    description: str = "Xcelium (xrun) simulator from Cadence"

    TOOL_OPTIONS: dict[str, dict[str, object]] = {
        "32bit": {
            "type": "bool",
            "desc": "Disable 64-bit mode",
        },
        "timescale": {
            "type": "str",
            "desc": "Default timescale for simulation",
        },
        "xrun_options": {
            "type": "str",
            "desc": "Additional run options for xrun",
            "list": True,
        },
        "gui": {
            "type": "bool",
            "desc": "Invoke the Graphical User Interface (GUI)",
        },
    }

    #: Map file type to xrun argument that will enable particular Verilog or VHDL features
    FILE_TYPE_TO_FEATURE_FLAG = {
        "verilogSource-95": "-v1995",
        "verilogSource-1995": "-v1995",
        "verilogSource-2001": "-v2001",
        "systemVerilogSource": "-sv",
        "vhdlSource-93": "-v93",
        "vhdlSource-1993": "-v93",
        "vhdlSource-2008": "-v200x",
        "vhdlSource-2019": "-v2019",
    }

    def setup(self, edam: dict[str, object]) -> None:
        """Setup the work root for the Cadence Xcelium logic simulator."""
        super().setup(edam)

        self.commands = EdaCommands()

        unused_files: list[dict[str, object]] = []
        """List of unused files."""

        incdirs: list[str] = []
        """List of include directories to include (Verilog/SystemVerilog only)."""

        depends: list[str] = ["xrun.f"]
        """List of file dependencies."""

        xmelab: list[str] = ["xrun", "-elaborate", "-f", "xrun.f"]
        """The simulator compilation and elaboration command to compile and elaborate design."""

        self.xrun_f: list[str] = []
        """The ``xrun.f`` file contains list of HDL source file to compile and elaborate."""

        self.xmsim: list[str] = ["xrun", "-R"]
        """The simulator runtime command with arguments to run compiled and elaborated design."""

        if not self.tool_options.get("32bit"):
            self.xrun_f.append("-64bit")

        timescale: str | None = self.tool_options.get("timescale")

        if timescale:
            self.xrun_f.extend(("-timescale", timescale))

        for f in self.files:
            file_type: str = f.get("file_type", "")
            file: str

            # Skip any file that is not tagged for simulation
            if "simulation" not in f.get("tags", ["simulation"]):
                unused_files.append(f)

            elif any(
                map(file_type.startswith, ("systemVerilogSource", "verilogSource"))
            ):
                library: str = f.get("logical_name", "worklib")
                file = f["name"]

                if not self._add_include_dir(f, incdirs, force_slash=True):
                    self.xrun_f.extend(("-makelib", library))

                    if file_type in self.FILE_TYPE_TO_FEATURE_FLAG:
                        self.xrun_f.append(self.FILE_TYPE_TO_FEATURE_FLAG[file_type])
                    elif file_type.startswith("systemVerilogSource"):
                        self.xrun_f.append("-sv")

                    for k, v in f.get("define", {}).items():
                        value = self._param_value_str(v, str_quote_style='"')
                        self.xrun_f.extend(("-define", f"{k}={value}"))

                    self.xrun_f.extend((file, "-endlib"))

                depends.append(file)

            elif file_type.startswith("vhdlSource"):
                library = f.get("logical_name", "worklib")
                file = f["name"]

                self.xrun_f.extend(("-makelib", library))

                if file_type in self.FILE_TYPE_TO_FEATURE_FLAG:
                    self.xrun_f.append(self.FILE_TYPE_TO_FEATURE_FLAG[file_type])

                self.xrun_f.extend((file, "-endlib"))
                depends.append(file)

            elif file_type == "tclSource":
                file = f["name"]
                self.xmsim.extend(("-input", file))
                depends.append(file)

            elif file_type == "dpiLibrary":
                file = f["name"]
                self.xmsim.extend(("-sv_lib", file))
                depends.append(file)

            else:
                unused_files.append(f)

        self.edam = edam.copy()
        self.edam["files"] = unused_files

        for incdir in incdirs:
            self.xrun_f.extend(("-incdir", incdir))

        for k, v in self.vlogdefine.items():
            value = self._param_value_str(v, str_quote_style='"')
            self.xrun_f.extend(("-define", f"{k}={value}"))

        for k, v in self.vlogparam.items():
            value = self._param_value_str(v, str_quote_style='"')
            self.xrun_f.extend(("-defparam", f"{self.toplevel}.{k}={value}"))

        for k, v in self.generic.items():
            value = self._param_value_str(v, str_quote_style='"')
            self.xrun_f.extend(("-generic", f"{k}={value}"))

        self.xrun_f.extend(("-top", self.toplevel))
        self.xrun_f.extend(self.tool_options.get("xrun_options", []))

        for k, v in self.plusarg.items():
            self.xmsim.append(f"+{k}={self._param_value_str(v)}")

        if self.tool_options.get("gui"):
            self.xmsim.append("-gui")

        target = "xcelium.d/run.d/hdl.var"
        self.commands.add(xmelab, [target], depends)
        self.commands.set_default_target(target)

    def write_config_files(self) -> None:
        """Write the ``xrun.f`` file to detect build configuration changes."""
        self.update_config_file("xrun.f", "\n".join(self.xrun_f) + "\n")

    def run(self) -> tuple[str, list[str], str]:
        """Run compiled and elaborated design with the Cadence Xcelium logic simulator."""
        return (self.xmsim[0], self.xmsim[1:], self.work_root)
