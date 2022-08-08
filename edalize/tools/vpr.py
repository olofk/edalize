# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import shutil
from edalize.tools.edatool import Edatool
from edalize.utils import EdaCommands
import logging
import pathlib
import os.path
import platform
import re
import subprocess


logger = logging.getLogger(__name__)


class Vpr(Edatool):
    """
     VPR tool Backend

    The VPR backend performs Packing, Placement, Routing & Timing Analysis.

    """

    TOOL_OPTIONS = {
        "arch_xml": {
            "type": "str",
            "desc": "Path to target architecture in XML format",
        },
        "input_file": {
            "type": "str",
            "desc": "The name of the input file for the make recipe",
        },
        "vpr_options": {
            "type": "str",
            "desc": "Additional options for VPR.",
            "list": True,
        },
        "gen_constraints": {
            "type": "str",
            "desc": "A list of arguments for the constraint generation scripts (for F4PGA/Symbiflow)",
            "list": True,
        },
    }

    def get_version(self):
        """
        Get tool version.

        This gets the VPR version by running "vpr --version" and
        parsing the output.
        If this command fails, "unknown" is returned.
        """
        version = "unknown"
        try:
            vpr_output = subprocess.Popen(
                ["vpr", "--version"], stdout=subprocess.PIPE, env=os.environ
            ).communicate()[0]
            version_exp = r"Version:(.*)"
            match = re.search(version_exp, str(vpr_output.decode()))
            if match:
                version = match.groups()[0]
        except Exception:
            logger.warning("Unable to recognize VPR version")
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
        incdirs = set()

        file_netlist = []
        timing_constraints = []

        for f in src_files:
            if f.file_type in ["blif", "eblif"]:
                file_netlist.append(f.name)
            if f.file_type in ["SDC"]:
                timing_constraints.append(f.name)

        if self.tool_options.get("input_file", "") != "":
            file_netlist += [self.tool_options.get("input_file", "")]

        arch_xml = self.tool_options.get("arch_xml")
        if not arch_xml:
            logger.error('Missing required "arch" parameter')

        _vo = self.tool_options.get("vpr_options")

        vpr_options = _vo if _vo else []
        sdc_opts = ["--sdc_file"] + timing_constraints if timing_constraints else []

        commands = EdaCommands()

        net_name = self.name + ".net"

        targets = net_name
        command = ["vpr", arch_xml] + file_netlist + ["--pack"]
        command += sdc_opts + vpr_options
        commands.add(command, [targets], file_netlist)

        # Load options for constraint generation
        gen_constraints = False
        gen_constraints_options = []
        first_script_arguments = []
        second_script_arguments = []
        first_script_output = ""
        second_script_output = ""
        if self.tool_options.get("gen_constraints"):
            gen_constraints = True
            gen_constraints_options = self.tool_options.get("gen_constraints")
            first_script_arguments = gen_constraints_options[0]
            second_script_arguments = gen_constraints_options[1]
            first_script_output = gen_constraints_options[2]
            second_script_output = gen_constraints_options[3]

        # Create constraint generation commands
        if self.tool_options.get("gen_constraints"):
            depends = net_name
            targets = first_script_output
            commands.add(first_script_arguments, [targets], [depends])

            depends = first_script_output
            targets = second_script_output
            commands.add(second_script_arguments, [targets], [depends])

        targets = self.name + ".place"
        if gen_constraints:
            depends = second_script_output
            command = (
                ["vpr", arch_xml]
                + file_netlist
                + [f"--fix_clusters {second_script_output}", "--place"]
            )
        else:
            depends = self.name + ".net"
            command = ["vpr", arch_xml] + file_netlist + ["--place"]
        command += sdc_opts + vpr_options
        commands.add(command, [targets], [depends])

        depends = self.name + ".place"
        targets = self.name + ".route"
        command = ["vpr", arch_xml] + file_netlist + ["--route"]
        command += sdc_opts + vpr_options
        commands.add(command, [targets], [depends])

        depends = self.name + ".route"
        targets = self.name + ".analysis"
        command = ["vpr", arch_xml] + file_netlist + ["--analysis"]
        command += sdc_opts + vpr_options
        commands.add(command, [targets], [depends])

        for ext in [".net", ".place", ".route", ".analysis"]:
            self.edam["files"].append(
                {"name": self.name + str(ext), "file_type": "vpr_" + str(ext[1:])}
            )

        self.commands = commands.commands
        commands.set_default_target(targets)
        commands.write(os.path.join(self.work_root, "Makefile"))

    def build(self):
        logger.info("Building")
        return ("make", self.args, self.work_root)
