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
        "gen_constraints": {
            "type": "bool",
            "desc": "If true, activates the symbiflow gen_constraints python script as part of the VPR process",
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

        depends = netlist_file
        targets = self.name + ".net"
        command = ["vpr", arch_xml, netlist_file, "--pack"]
        command += sdc_opts + vpr_options
        commands.add(command, [targets], [depends])

        # Run generate constraints script of flag set to true
        if self.tool_options.get("gen_constraints", False):
            depends = self.name + ".net"
            targets = "${IOPLACE_FILE}"
            commands.add(
                [
                    "${PYTHON}",
                    "${IOGEN}",
                    "--blif ${OUT_EBLIF}",
                    "--map ${PINMAP_FILE}",
                    "--net ${NET_FILE}",
                    "> ${IOPLACE_FILE}",
                ],
                [targets],
                [depends],
            )

            depends = "${IOPLACE_FILE}"
            targets = "${CONSTR_FILE}"
            commands.add(
                [
                    "${PYTHON}",
                    "${CONSTR_GEN}",
                    "--net ${NET_FILE}",
                    "--arch ${ARCH_DEF}",
                    "--blif ${OUT_EBLIF}",
                    "--vpr_grid_map ${VPR_GRID_MAP}",
                    "--input ${IOPLACE_FILE}",
                    "--db_root ${DATABASE_DIR} " "--part ${PART}",
                    "> ${CONSTR_FILE}",
                ],
                [targets],
                [depends],
            )

        targets = self.name + ".place"
        command = ["vpr", arch_xml, netlist_file]
        # Modify place stage if running generate constraints script
        if self.tool_options.get("gen_constraints", False):
            depends = "${CONSTR_FILE}"
            command += ["--fix_clusters ${CONSTR_FILE}"]
        else:
            depends = self.name + ".net"
        command += ["--place"]
        command += sdc_opts + vpr_options
        commands.add(command, [targets], [depends])

        depends = self.name + ".place"
        targets = self.name + ".route"
        command = ["vpr", arch_xml, netlist_file, "--route"]
        command += sdc_opts + vpr_options
        commands.add(command, [targets], [depends])

        depends = self.name + ".route"
        targets = self.name + ".analysis"
        command = ["vpr", arch_xml, netlist_file, "--analysis"]
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
