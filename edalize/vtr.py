# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import shutil
from edalize.edatool import Edatool
import logging
import pathlib


logger = logging.getLogger(__name__)

""" VTR Backend

To run this you will need to provide at minimum:
- Single Verilog design source (multiple source files not yet supported)

If VTR is not on your PATH (vtr/vtr_flow/scripts) then you can provide:
- vtr_pth (path to compiled VTR source tree)

"""


class Vtr(Edatool):
    @classmethod
    def get_doc(cls, api_ver):
        if api_ver == 0:
            return {
                "description": "The VTR backend runs the VTR open-source FPGA CAD tool, consisting of synthesis, tech mapping, packing, placement and routintg.",
                "members": [
                    {
                        "name": "vtr_path",
                        "type": "String",
                        "desc": "The path to the VTR tool installation",
                    },
                    {
                        "name": "route_chan_width",
                        "type": "Integer",
                        "desc": "Routing channel width.  If not provided, a minimum channel width will be determined, and then a relaxation factor will be added.",
                    },
                ],
            }

    def configure_main(self):
        commands = self.EdaCommands()
        work_root = pathlib.Path(self.work_root)


        ############ Find VTR Tool #############
        vtr_path = None
        run_vtr_flow_py_path = "run_vtr_flow.py"

        # Check for vtr_path tool_option
        if "vtr_path" in self.tool_options:
            vtr_path = pathlib.Path(self.tool_options["vtr_path"])            

            # Make sure vtr_path points to a directory with a run_vtr_flow.py
            # script in the correct location
            run_vtr_flow_py_path = vtr_path / "vtr_flow" / "scripts" / "run_vtr_flow.py"
            if not run_vtr_flow_py_path.is_file():
                logger.warning("vtr_path invalid (" + str(run_vtr_flow_py_path) + " does not exist)")

        ############ Parse all files #############

        # Default files
        verilog_path = None
        if vtr_path:
            arch_path = vtr_path / "vtr_flow" / "arch" / "timing" / "k6_N10_mem32K_40nm.xml"
        else:
            arch_path = pathlib.Path("k6_N10_mem32K_40nm.xml")

        # Check all input file types
        for f in self.files:
            if f["file_type"].startswith("verilogSource"):
                if verilog_path:
                    logger.warning("Ignoring extra Verilog file", f)
                else:
                    verilog_path = pathlib.Path(f["name"])
            elif f["file_type"] == "vtr_arch":
                arch_path = pathlib.Path(f["name"])
            else:
                logger.warning("Unsupported file " + str(f))

        # Validate verilog file exists
        if verilog_path is None:
            logger.error("Missing required Verilog source file")
            return
        elif not verilog_path.is_file():
            logger.warning("Verilog source file " + str(verilog_path) + " does not exist")

        # Validate arch file exists
        if not arch_path.is_file():
            logger.warning("Architecture XML file " + str(arch_path) + " does not exist.")

        ############ Build Makefile #############

        # Build Makefile for running run_vtr_flow.py
        route_file_path = pathlib.Path("temp") / (self.name + ".route")

        # Default vtr_flow runner
        cmd = [
            str(run_vtr_flow_py_path),
            str(verilog_path),
            str(arch_path),
        ]
        if "route_chan_width" in self.tool_options:
            cmd += ["--route_chan_width", str(self.tool_options["route_chan_width"])]
        commands.add(cmd, [str(route_file_path)], ())

        commands.set_default_target(str(route_file_path))
        commands.write(str(work_root / "Makefile"))

    def build_main(self):
        logger.info("Building")

        self._run_tool("make", quiet=True)
