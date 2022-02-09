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

        arch_xml = self.tool_options.get("arch_xml")
        if not arch_xml:
            logger.error('Missing required "arch" parameter')

        _vo = self.tool_options.get("vpr_options")

        vpr_options = _vo if _vo else []
        sdc_opts = ["--sdc_file"] + timing_constraints if timing_constraints else []

        commands = EdaCommands()

        depends = self.name + ".blif"
        targets = self.name + ".net"
        command = ["vpr", arch_xml, self.name + ".blif", "--pack"]
        command += sdc_opts + vpr_options
        commands.add(command, [targets], [depends])

        depends = self.name + ".net"
        targets = self.name + ".place"
        command = ["vpr", arch_xml, self.name + ".blif", "--place"]
        command += sdc_opts + vpr_options
        commands.add(command, [targets], [depends])

        depends = self.name + ".place"
        targets = self.name + ".route"
        command = ["vpr", arch_xml, self.name + ".blif", "--route"]
        command += sdc_opts + vpr_options
        commands.add(command, [targets], [depends])

        depends = self.name + ".route"
        targets = self.name + ".analysis"
        command = ["vpr", arch_xml, self.name + ".blif", "--analysis"]
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
