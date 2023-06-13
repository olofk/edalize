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
        "generate_constraints": {
            "type": "list",
            "desc": "A list of values used to generate constraints at the place stage (used by F4PGA flow)",
        },
        "vpr_options": {
            "type": "str",
            "desc": "Additional options for VPR.",
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

    def setup(self, edam):
        """
        Configuration is the first phase of the build.

        This writes the project TCL files and Makefile. It first collects all
        sources, IPs and constraints and then writes them to the TCL file along
        with the build steps.
        """
        super().setup(edam)

        netlist_file = ""
        timing_constraints = []

        for f in self.files:
            file_type = f.get("file_type", "")

            if file_type in ["blif", "eblif"]:
                if netlist_file:
                    raise RuntimeError(
                        "VPR only supports one netlist file. Found {} and {}".format(
                            netlist_file, f["name"]
                        )
                    )
                netlist_file = f["name"]
            if file_type in ["SDC"]:
                timing_constraints.append(f.name)

        arch_xml = self.tool_options.get("arch_xml")
        if not arch_xml:
            logger.error('Missing required "arch" parameter')

        _vo = self.tool_options.get("vpr_options")

        vpr_options = _vo if _vo else []
        sdc_opts = ["--sdc_file"] + timing_constraints if timing_constraints else []

        commands = EdaCommands()

        # First, check if gen_constraint value list is passed in and is the correct size
        gen_constr_list = self.tool_options.get("generate_constraints", [])

        depends = netlist_file
        targets = self.name + ".net"
        command = ["vpr", arch_xml, netlist_file, "--pack"]
        command += (
            sdc_opts + vpr_options + [";", "mv", "vpr_stdout.log", "pack.log"]
            if gen_constr_list
            else []
        )
        commands.add(command, [targets], [depends])

        # Run generate constraints script if correct list exists
        constraints_file = "constraints.place"
        if gen_constr_list:
            depends = self.name + ".net"
            targets = constraints_file
            commands.add(
                [
                    "python3",
                    "-m f4pga.wrappers.sh.generate_constraints",
                    " ".join(gen_constr_list),
                ],
                [targets],
                [depends],
            )

        depends = [self.name + ".net"]
        targets = self.name + ".place"
        command = ["vpr", arch_xml, netlist_file]

        # Modify place stage if running generate constraints script
        if gen_constr_list:
            depends += [constraints_file]
            command += [f"--fix_clusters {constraints_file}"]

        command += ["--place"]
        command += (
            sdc_opts + vpr_options + [";", "mv", "vpr_stdout.log", "place.log"]
            if gen_constr_list
            else []
        )
        commands.add(command, [targets], depends)

        depends = self.name + ".place"
        targets = self.name + ".route"
        command = ["vpr", arch_xml, netlist_file, "--route"]
        command += (
            sdc_opts + vpr_options + [";", "mv", "vpr_stdout.log", "route.log"]
            if gen_constr_list
            else []
        )
        commands.add(command, [targets], [depends])

        depends = self.name + ".route"
        targets = self.name + ".analysis"
        command = ["vpr", arch_xml, netlist_file, "--analysis"]
        command += (
            sdc_opts + vpr_options + [";", "mv", "vpr_stdout.log", "analysis.log"]
            if gen_constr_list
            else []
        )
        commands.add(command, [targets], [depends])

        for ext in [".net", ".place", ".route", ".analysis"]:
            self.edam["files"].append(
                {"name": self.name + str(ext), "file_type": "vpr_" + str(ext[1:])}
            )

        commands.set_default_target(targets)
        self.commands = commands

    def build(self):
        logger.info("Building")
        return ("make", self.args, self.work_root)
