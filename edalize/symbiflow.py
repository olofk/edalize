import logging
import os.path
import platform
import re
import subprocess

from edalize.edatool import Edatool
from edalize.yosys import Yosys
from importlib import import_module

logger = logging.getLogger(__name__)

""" Symbiflow backtend

A core (usually the system core) can add the following files:

- Standard design sources (Verilog only)

- Constraints: unmanaged constraints with file_type SDC, pin_constraints with file_type PCF and placement constraints with file_type xdc

"""


class Symbiflow(Edatool):

    argtypes = ["vlogdefine", "vlogparam", "generic"]

    @classmethod
    def get_doc(cls, api_ver):
        if api_ver == 0:
            symbiflow_help = {
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
                    {
                        "name": "vendor",
                        "type": "String",
                        "desc": 'Target architecture. Currently only "xilinx" is supported',
                    },
                    {
                        "name": "pnr",
                        "type": "String",
                        "desc": 'Place and Route tool. Currently only "vpr" is supported',
                    },
                    {
                        "name": "vpr_options",
                        "type": "String",
                        "desc": "Additional vpr tool options. If not used, default options for the tool will be used",
                    },
                    {
                        "name" : "environment_script",
                        "type" : "String",
                        "desc" : "Optional bash script that will be sourced before each build step."
                    },
                ]
            }

            symbiflow_members = symbiflow_help["members"]

            return {
                "description": "The Symbiflow backend executes Yosys sythesis tool and VPR place and route. It can target multiple different FPGA vendors",
                "members": symbiflow_members,
            }

    def get_version(self):
        return "1.0"

    def configure_vpr(self):
        (src_files, incdirs) = self._get_fileset_files(force_slash=True)

        has_vhdl = "vhdlSource" in [x.file_type for x in src_files]
        has_vhdl2008 = "vhdlSource-2008" in [x.file_type for x in src_files]

        if has_vhdl or has_vhdl2008:
            logger.error("VHDL files are not supported in Yosys")
        file_list = []
        timing_constraints = []
        pins_constraints = []
        placement_constraints = []
        user_files = []

        for f in src_files:
            if f.file_type in ["verilogSource"]:
                file_list.append(f.name)
            if f.file_type in ["SDC"]:
                timing_constraints.append(f.name)
            if f.file_type in ["PCF"]:
                pins_constraints.append(f.name)
            if f.file_type in ["xdc"]:
                placement_constraints.append(f.name)
            if f.file_type in ["user"]:
                user_files.append(f.name)

        part = self.tool_options.get('part', None)
        package = self.tool_options.get('package', None)
        vendor = self.tool_options.get('vendor', None)

        if not part:
            logger.error('Missing required "part" parameter')
        if not package:
            logger.error('Missing required "package" parameter')

        if vendor == 'xilinx':
            if 'xc7a' in part:
                bitstream_device = 'artix7'
            if 'xc7z' in part:
                bitstream_device = 'zynq7'
            if 'xc7k' in part:
                bitstream_device = 'kintex7'

            partname = part + package

            # a35t are in fact a50t
            # leave partname with 35 so we access correct DB
            if part == 'xc7a35t':
                part = 'xc7a50t'
            device_suffix = 'test'
        elif vendor == 'quicklogic':
            partname = package
            device_suffix = 'wlcsp'
            bitstream_device = part + "_" + device_suffix

        vpr_options = self.tool_options.get("vpr_options", None)


        # Optional script that will be sourced right before executing each build step in Makefile
        # This script can for example setup enviroment variables or conda enviroment.
        # This file needs to be a bash file
        environment_script = self.tool_options.get('environment_script', None)

        makefile_params = {
            "top": self.toplevel,
            "sources": " ".join(file_list),
            "partname": partname,
            "part": part,
            "bitstream_device": bitstream_device,
            "sdc": " ".join(timing_constraints),
            "pcf": " ".join(pins_constraints),
            "xdc": " ".join(placement_constraints),
            "vpr_options": vpr_options,
            "device_suffix": device_suffix,
            "toolchain_prefix": 'symbiflow_',
            "environment_script": environment_script,
            "vendor": vendor,
        }
        self.render_template("symbiflow-vpr-makefile.j2", "Makefile", makefile_params)

    def configure_main(self):
        if self.tool_options.get("pnr") == "vtr":
            self.configure_vpr()
        else:
            logger.error("VPR is the only P&R tool currently supported in SymbiFlow")

    def run_main(self):
        logger.info("Programming")
