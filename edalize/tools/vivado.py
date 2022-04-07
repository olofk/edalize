# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import logging
import os.path
import platform
import re
import subprocess

from edalize.tools.edatool import Edatool
from edalize.utils import EdaCommands

logger = logging.getLogger(__name__)


class Vivado(Edatool):
    """
    Vivado Backend.

    A core (usually the system core) can add the following files:

    * Standard design sources
    * Constraints: Supply xdc files with file_type=xdc or unmanaged constraints with file_type SDC
    * IP: Supply the IP core xci file with file_type=xci and other files (like .prj) as file_type=user
    """

    argtypes = ["vlogdefine", "vlogparam", "generic"]

    TOOL_OPTIONS = {
        "part": {
            "type": "String",
            "desc": "FPGA part number (e.g. xc7a35tcsg324-1)",
        },
        "synth": {
            "type": "String",
            "desc": "Synthesis tool. Allowed values are vivado or none.",
        },
        "board_part": {
            "type": "String",
            "desc": "Board part number (e.g. xilinx.com:kc705:part0:0.9)",
        },
        "board_repo_paths": {
            "type": "String",
            "desc": "Board repository paths. A list of paths to search for board files.",
        },
        "pnr": {
            "type": "String",
            "desc": "P&R tool. Allowed values are vivado (default) and none (to just run synthesis)",
        },
        "jobs": {
            "type": "Integer",
            "desc": "Number of jobs. Useful for parallelizing OOC (Out Of Context) syntheses.",
        },
        "jtag_freq": {
            "type": "Integer",
            "desc": "The frequency for jtag communication",
        },
        "source_mgmt_mode": {
            "type": "String",
            "desc": "Source managment mode. Allowed values are None (unmanaged, default), DisplayOnly (automatically update sources) and All (automatically update sources and compile order)",
        },
        "hw_target": {
            "type": "Description",
            "desc": "A pattern matching a board identifier. Refer to the Vivado documentation for ``get_hw_targets`` for details. Example: ``*/xilinx_tcf/Digilent/123456789123A``",
        },
    }

    def get_version(self):
        """
        Get tool version.

        This gets the Vivado version by running vivado -version and
        parsing the output. If this command fails, "unknown" is returned.
        """
        version = "unknown"
        try:
            vivado_text = subprocess.Popen(
                ["vivado", "-version"], stdout=subprocess.PIPE, env=os.environ
            ).communicate()[0]
            version_exp = r"Vivado.*(?P<version>v.*) \(.*"

            match = re.search(version_exp, str(vivado_text))
            if match is not None:
                version = match.group("version")
        except Exception:
            logger.warning("Unable to recognize Vivado version")

        return version

    def configure(self, edam):
        """
        Configuration is the first phase of the build.

        This writes the project TCL files and Makefile. It first collects all
        sources, IPs and constraints and then writes them to the TCL file along
        with the build steps.
        """
        super().configure(edam)
        src_files = []
        incdirs = []
        edif_files = []
        has_vhdl2008 = False
        has_xci = False
        unused_files = []
        bd_files = []

        for f in self.files:
            file_type = f.get("file_type", "")
            cmd = ""
            if file_type.startswith("verilogSource"):
                cmd = "read_verilog"
            elif file_type.startswith("systemVerilogSource"):
                cmd = "read_verilog -sv"
            elif file_type == "tclSource":
                cmd = "source"
            elif file_type == "edif":
                cmd = "read_edif"
                edif_files.append(f["name"])
            elif file_type.startswith("vhdlSource"):
                cmd = "read_vhdl"
                if file_type == "vhdlSource-2008":
                    has_vhdl2008 = True
                    cmd += " -vhdl2008"
                if f.get("logical_name"):
                    cmd += " -library " + f["logical_name"]
            elif file_type == "xci":
                cmd = "read_ip"
                has_xci = True
            elif file_type == "xdc":
                cmd = "read_xdc"
            elif file_type == "SDC":
                cmd = "read_xdc -unmanaged"
            elif file_type == "mem":
                cmd = "read_mem"
            elif file_type == "bd":
                cmd = "read_bd"
                bd_files.append(f["name"])

            if cmd:
                if not self._add_include_dir(f, incdirs):
                    src_files.append(cmd + " {" + f["name"] + "}")
            else:
                unused_files.append(f)
        template_vars = {
            "name": self.name,
            "src_files": "\n".join(src_files),
            "incdirs": incdirs + ["."],
            "tool_options": self.tool_options,
            "toplevel": self.toplevel,
            "vlogparam": self.vlogparam,
            "vlogdefine": self.vlogdefine,
            "generic": self.generic,
            "netlist_flow": bool(edif_files),
            "has_vhdl2008": has_vhdl2008,
            "has_xci": has_xci,
            "bd_files": bd_files,
        }
        self.render_template("vivado-project.tcl.j2", self.name + ".tcl", template_vars)

        jobs = self.tool_options.get("jobs", None)

        run_template_vars = {"jobs": " -jobs " + str(jobs) if jobs is not None else ""}

        self.render_template(
            "vivado-run.tcl.j2", self.name + "_run.tcl", run_template_vars
        )

        synth_template_vars = {
            "jobs": " -jobs " + str(jobs) if jobs is not None else ""
        }

        self.render_template(
            "vivado-synth.tcl.j2", self.name + "_synth.tcl", synth_template_vars
        )
        # Write Makefile
        commands = EdaCommands()

        vivado_command = ["vivado", "-notrace", "-mode", "batch", "-source"]

        # Create project file
        project_file = self.name + ".xpr"
        tcl_file = [self.name + ".tcl"]
        commands.add(vivado_command + tcl_file, [project_file], tcl_file + edif_files)
        synth = self.tool_options.get("synth", "vivado")
        if synth == "vivado":
            depends = [f"{self.name}_synth.tcl", project_file]
            targets = [f"{self.name}.runs/synth_1/__synthesis_is_complete__"]
            commands.add(vivado_command + depends, targets, depends)
        else:
            targets = edif_files

        commands.add([], ["synth"], targets)

        # Bitstream generation
        run_tcl = self.name + "_run.tcl"
        depends = [run_tcl, project_file]
        bitstream = self.name + ".bit"
        commands.add(vivado_command + depends, [bitstream], depends)

        commands.add(["vivado", project_file], ["build-gui"], [project_file])

        depends = [self.name + "_pgm.tcl", bitstream]
        command = [
            "vivado",
            "-quiet",
            "-nolog",
            "-notrace",
            "-mode",
            "batch",
            "-source",
            f"{self.name}_pgm.tcl",
            "-tclargs",
        ]
        part = self.tool_options.get("part", "")
        command += [part] if part else []
        command += [bitstream]
        commands.add(command, ["pgm"], depends)

        commands.set_default_target(bitstream)
        commands.write(os.path.join(self.work_root, "Makefile"))
        self.commands = commands.commands
        self.render_template("vivado-program.tcl.j2", self.name + "_pgm.tcl")

    def build(self):
        logger.info("Building")
        args = []
        if "pnr" in self.tool_options:
            if self.tool_options["pnr"] == "vivado":
                pass
            elif self.tool_options["pnr"] == "none":
                args.append("synth")
        return ("make", self.args, self.work_root)

    def run(self):
        """
        Program the FPGA.

        For programming the FPGA a vivado tcl script is written that searches for the
        correct FPGA board and then downloads the bitstream. The tcl script is then
        executed in Vivado's batch mode.
        """
        if "pnr" in self.tool_options:
            if self.tool_options["pnr"] == "vivado":
                pass
            elif self.tool_options["pnr"] == "none":
                return

        return ("make", ["pgm"], self.work_root)
