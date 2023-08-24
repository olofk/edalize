# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import logging
import os.path
import platform
import re
import subprocess

from edalize.edatool import Edatool
from edalize.yosys import Yosys
from edalize.flows.vivado import Vivado as Vivado_underlying

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

    @classmethod
    def get_doc(cls, api_ver):
        if api_ver == 0:
            return {
                "description": "The Vivado backend executes Xilinx Vivado to build systems and program the FPGA",
                "lists": [
                    {
                        "name": "board_repo_paths",
                        "type": "String",
                        "desc": "Board repository paths. A list of paths to search for board files.",
                    },
                ],
                "members": [
                    {
                        "name": "part",
                        "type": "String",
                        "desc": "FPGA part number (e.g. xc7a35tcsg324-1)",
                    },
                    {
                        "name": "board_part",
                        "type": "String",
                        "desc": "Board part number (e.g. xilinx.com:kc705:part0:0.9)",
                    },
                    {
                        "name": "synth",
                        "type": "String",
                        "desc": "Synthesis tool. Allowed values are vivado (default) and yosys.",
                    },
                    {
                        "name": "pnr",
                        "type": "String",
                        "desc": "P&R tool. Allowed values are vivado (default) and none (to just run synthesis)",
                    },
                    {
                        "name": "pgm",
                        "type": "String",
                        "desc": "Programming tool. Default is none, set to 'vivado' to program the FPGA in the run stage.",
                    },
                    {
                        "name": "jobs",
                        "type": "Integer",
                        "desc": "Number of jobs. Useful for parallelizing OOC (Out Of Context) syntheses.",
                    },
                    {
                        "name": "jtag_freq",
                        "type": "Integer",
                        "desc": "The frequency for jtag communication",
                    },
                    {
                        "name": "source_mgmt_mode",
                        "type": "String",
                        "desc": "Source managment mode. Allowed values are None (unmanaged, default), DisplayOnly (automatically update sources) and All (automatically update sources and compile order)",
                    },
                    {
                        "name": "hw_target",
                        "type": "Description",
                        "desc": "A pattern matching a board identifier. Refer to the Vivado documentation for ``get_hw_targets`` for details. Example: ``*/xilinx_tcf/Digilent/123456789123A``",
                    },
                    {
                        "name": "frontends",
                        "type": "String",
                        "desc": "",
                    },
                ],
            }

    def __init__(self, edam=None, work_root=None, eda_api=None, verbose=True):
        super().__init__(edam, work_root, eda_api, verbose)
        edam["flow_options"] = edam["tool_options"]["vivado"]
        self.vivado = Vivado_underlying(edam, work_root, verbose)

    def configure_main(self):
        self.vivado.configure()

    def build_main(self):
        logger.info("Building")
        args = []
        if "pnr" in self.tool_options:
            if self.tool_options["pnr"] == "vivado":
                pass
            elif self.tool_options["pnr"] == "none":
                args.append("synth")
        self._run_tool("make", args)

    def run_main(self):
        """
        Program the FPGA.

        For programming the FPGA a vivado tcl script is written that searches for the
        correct FPGA board and then downloads the bitstream. The tcl script is then
        executed in Vivado's batch mode.
        """
        if ("pgm" not in self.tool_options) or (self.tool_options["pgm"] != "vivado"):
            return

        self._run_tool("make", ["pgm"])

    def build_pre(self):
        pass

    def build_post(self):
        pass
