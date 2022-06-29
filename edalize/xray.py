# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import logging
import os.path

from edalize.edatool import Edatool
from edalize.utils import EdaCommands
from edalize.nextpnr import Nextpnr
from edalize.yosys import Yosys

logger = logging.getLogger(__name__)


class Xray(Edatool):

    argtypes = ["vlogdefine", "vlogparam"]

    @classmethod
    def get_doc(cls, api_ver):
        if api_ver == 0:
            options = {
                "members": [
                    {
                        "name": "package",
                        "type": "String",
                        "desc": "FPGA chip package (e.g. clg400-1)",
                    },
                    {
                        "name": "part",
                        "type": "String",
                        "desc": "FPGA part type (e.g. xc7a50t)",
                    },
                ],
                "lists": [
                    {
                        "name": "nextpnr_options",
                        "type": "String",
                        "desc": "Additional options for nextpnr",
                    }
                ],
            }

            Edatool._extend_options(options, Yosys)

            return {
                "description": "Project X-Ray enables a fully open-source flow for Xilinx 7-series FPGAs using Yosys for Verilog synthesis and nextpnr for place and route",
                "members": options["members"],
                "lists": options["lists"],
            }

    def configure_main(self):
        (src_files, incdirs) = self._get_fileset_files(force_slash=True)
        # Pass tool options to yosys and nextpnr
        self.edam["tool_options"] = {
            "yosys": {
                "arch": "xilinx",
                "prj": "xray",
                "output_format": "json",
                "yosys_synth_options": self.tool_options.get("yosys_synth_options", [])
                + ["-arch", "xc7"],
                "yosys_as_subtool": True,
                "yosys_template": self.tool_options.get("yosys_template"),
            },
        }

        yosys = Yosys(self.edam, self.work_root)
        yosys.configure()

        # chipdb = None
        placement_constraints = []

        for f in src_files:
            # if f.file_type in ["bba"]:
            #     chipdb = f.name
            if f.file_type.upper() in ["XDC"]:
                placement_constraints.append(f.name)
            else:
                continue

        # if not chipdb:
        #     logger.error("Missing required chipdb file")

        if placement_constraints == []:
            logger.error("Missing required XDC file(s)")

        part = self.tool_options.get("part") + self.tool_options.get("package")
        if "xc7a" in part:
            bitstream_device = "artix7"
        if "xc7z" in part:
            bitstream_device = "zynq7"
        if "xc7k" in part:
            bitstream_device = "kintex7"

        xdcs = []
        for x in placement_constraints:
            xdcs += ["--xdc", x]

        nextpnr_options = self.tool_options.get("nextpnr_options", [])

        # Write Makefile
        commands = EdaCommands()

        # commands.add_var("export CHIPDB=/opt/nextpnr/xilinx-chipdb")
        # commands.add_var("export DB_DIR=/opt/nextpnr/prjxray-db")

        commands.commands = yosys.commands

        # Xilinx nextpnr (until there is a proper backend for it)
        depends = self.name + ".json"
        targets = self.name + ".fasm"
        command = ["nextpnr-xilinx"]
        command += nextpnr_options
        command += ["--chipdb", "\\$${CHIPDB}/" + part + ".bin"]  # Use chipdb file?!?
        command += xdcs
        command += ["--json", depends]
        command += ["--write", self.name + "_routed.json"]
        command += ["--fasm", targets]
        commands.add(command, [targets], [depends])

        # Generate Frames file
        depends = self.name + ".fasm"
        targets = self.name + ".frames"
        command = ["fasm2frames"]
        command += ["--part", part]
        command += ["--db-root", "\\$${DB_DIR}/" + bitstream_device]
        command += [depends, ">", targets]
        commands.add(command, [targets], [depends])

        # # Generate Bitstream
        depends = self.name + ".frames"
        targets = self.name + ".bit"
        command = ["xc7frames2bit"]
        command += [
            "--part_file",
            "\\$${DB_DIR}/" + bitstream_device + "/" + part + "/part.yaml",
        ]
        command += ["--part_name", part]
        command += ["--frm_file", depends]
        command += ["--output_file", targets]
        commands.add(command, [targets], [depends])

        # Write Makefile
        commands.set_default_target(self.name + ".bit")
        commands.write(os.path.join(self.work_root, "Makefile"))
