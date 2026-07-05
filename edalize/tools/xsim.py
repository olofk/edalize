# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import shlex
import logging

from edalize.tools.edatool import Edatool
from edalize.utils import EdaCommands

logger = logging.getLogger(__name__)


class Xsim(Edatool):
    description: str = "XSim logic simulator from the AMD/Xilinx Vivado suite"

    TOOL_OPTIONS: dict[str, dict[str, object]] = {
        "xelab_options": {
            "type": "str",
            "desc": "Additional options for compilation with xelab",
            "list": True,
        },
        "xsim_options": {
            "type": "str",
            "desc": "Additional run options for xsim",
            "list": True,
        },
        "gui": {
            "type": "bool",
            "desc": "Invoke the Graphical User Interface (GUI)",
        },
    }

    def setup(self, edam: dict[str, object]) -> None:
        """Setup the work root for the AMD/Xilinx XSim logic simulator."""
        super().setup(edam)

        self.commands = EdaCommands()

        unused_files: list[dict[str, object]] = []
        """List of unused files."""

        incdirs: list[str] = []
        """List of include directories to include (Verilog/SystemVerilog only)."""

        libraries: list[str] = []
        """List of logical libraries to include."""

        depends: list[str] = ["xsim.prj"]
        """List of file dependencies."""

        xelab: list[str] = ["xelab", "--prj", "xsim.prj"]
        """The simulator compilation and elaboration command to compile and elaborate design."""

        self.xsim_prj: list[str] = []
        """The ``xsim.prf`` file contains list of HDL source file to compile and elaborate."""

        self.xsim: list[str] = ["xsim"]
        """The simulator runtime command with arguments to run compiled and elaborated design."""

        for f in self.files:
            file_type: str = f.get("file_type", "")
            file: str

            # Skip any file that is not tagged for simulation
            if "simulation" not in f.get("tags", ["simulation"]):
                unused_files.append(f)

            elif any(
                map(file_type.startswith, ("systemVerilogSource", "verilogSource"))
            ):
                library: str = f.get("logical_name", "work")
                file = f["name"]

                if library not in libraries:
                    libraries.append(library)

                if not self._add_include_dir(f, incdirs, force_slash=True):
                    cmd: list[str]

                    if file_type.startswith("verilog"):
                        cmd = ["verilog", library, file]
                    else:
                        cmd = ["sv", library, file]

                    for k, v in f.get("define", {}).items():
                        cmd.extend(("-d", f"{k}={self._param_value_str(v)}"))

                    self.xsim_prj.append(shlex.join(cmd))

                depends.append(file)

            elif file_type.startswith("vhdlSource"):
                library = f.get("logical_name", "work")
                file = f["name"]

                if library not in libraries:
                    libraries.append(library)

                if file_type == "vhdlSource-2008":
                    cmd = ["vhdl2008", library, file]
                else:
                    cmd = ["vhdl", library, file]

                self.xsim_prj.append(shlex.join(cmd))
                depends.append(file)

            elif file_type == "tclSource":
                file = f["name"]
                self.xsim.extend(("--tclbatch", file))
                depends.append(file)

            elif file_type == "dpiLibrary":
                file = f["name"]
                self.xsim.extend(("--sv_lib", file))
                depends.append(file)

            else:
                unused_files.append(f)

        self.edam = edam.copy()
        self.edam["files"] = unused_files

        for library in libraries:
            xelab.extend(("--lib", library))

        for incdir in incdirs:
            xelab.extend(("--include", incdir))

        for k, v in self.vlogdefine.items():
            xelab.extend(("--define", f"{k}={self._param_value_str(v)}"))

        for k, v in self.vlogparam.items():
            xelab.extend(("--generic_top", f"{k}={self._param_value_str(v)}"))

        for k, v in self.generic.items():
            xelab.extend(("--generic_top", f"{k}={self._param_value_str(v)}"))

        xelab.extend(self.tool_options.get("xelab_options", []))
        xelab.append(self.toplevel)

        for k, v in self.plusarg.items():
            self.xsim.extend(("--testplusarg", f"{k}={v}"))

        if self.tool_options.get("gui"):
            self.xsim.append("--gui")
        else:
            self.xsim.append("--runall")

        self.xsim.extend(self.tool_options.get("xsim_options", []))
        self.xsim.append(self.toplevel)

        library, _, toplevel = self.toplevel.rpartition(".")

        if not library:
            library = "work"

        target = f"xsim.dir/{library}.{toplevel}/xsimk"
        self.commands.add(xelab, [target], depends)
        self.commands.set_default_target(target)

    def write_config_files(self) -> None:
        """Write the ``xsim.prj`` file to detect build configuration changes."""
        self.update_config_file("xsim.prj", "\n".join(self.xsim_prj) + "\n")

    def run(self) -> tuple[str, list[str], str]:
        """Run compiled and elaborated design with the AMD/Xilinx XSim logic simulator."""
        return (self.xsim[0], self.xsim[1:], self.work_root)
