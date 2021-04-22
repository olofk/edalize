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
from importlib import import_module

logger = logging.getLogger(__name__)

""" Symbiflow backend

A core (usually the system core) can add the following files:

- Standard design sources (Verilog only)

- Constraints: unmanaged constraints with file_type SDC, pin_constraints with file_type PCF and placement constraints with file_type xdc

"""


class Symbiflow(Edatool):

    argtypes = ["vlogdefine", "vlogparam", "generic"]
    archs = ["xilinx", "fpga_interchange"]
    fpga_interchange_families = ["xc7"]

    @classmethod
    def get_doc(cls, api_ver):
        if api_ver == 0:
            symbiflow_help = {
                "members": [
                    {
                        "name" : "arch",
                        "type" : "String",
                        "desc" : "Target architecture. Legal values are *xilinx* and *fpga_interchange* (this is relevant only for Nextpnr variant)."
                    },
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
                        "desc": 'Place and Route tool. Currently only "vpr"/"vtr" and "nextpnr" are supported',
                    },
                    {
                        "name": "vpr_options",
                        "type": "String",
                        "desc": "Additional options for VPR tool. If not used, default options for the tool will be used",
                    },
                    {
                        "name": "nextpnr_options",
                        "type": "String",
                        "desc": "Additional options for Nextpnr tool. If not used, default options for the tool will be used",
                    },
                    {
                        "name": "fasm2bels",
                        "type": "Boolean",
                        "desc": "Value to state whether fasm2bels is to be used."
                    },
                    {
                        "name": "dbroot",
                        "type": "String",
                        "desc": "Path to the database root (needed by fasm2bels)."
                    },
                    {
                        "name": "clocks",
                        "type": "dict",
                        "desc": "Clocks to be added for having tools correctly handling timing based routing."
                    },
                    {
                        "name": "seed",
                        "type": "String",
                        "desc": "Seed assigned to the PnR tool."
                    },
                ]
            }

            symbiflow_members = symbiflow_help["members"]

            return {
                "description": "The Symbiflow backend executes Yosys sythesis tool and VPR/Nextpnr place and route. It can target multiple different FPGA vendors",
                "members": symbiflow_members,
            }

    def get_version(self):
        return "1.0"

    def configure_nextpnr(self):
        (src_files, incdirs) = self._get_fileset_files(force_slash=True)
        vendor = self.tool_options.get("vendor")
        arch = self.tool_options.get("arch")
        if arch not in self.archs:
            logger.error('Missing or invalid "arch" parameter: {} in "tool_options"'.format(arch))
        fasm2bels = self.tool_options.get("fasm2bels", False)
        if fasm2bels and arch is "fpga_interchange":
            logger.error('"fasm2bels" option is not supported for "fpga_interchange" arch')

        # Yosys configuration
        yosys_synth_options = self.tool_options.get("yosys_synth_options", "")
        yosys_template = self.tool_options.get("yosys_template")
        # If yosys_template is not provided use the default one for a specific workflow
        if yosys_template is None and arch == "fpga_interchange":
            yosys_template = self.get_template_path("yosys-script-nextpnr-fpga_interchange-tcl.j2")
        elif yosys_template is None and arch == "xilinx" and fasm2bels:
            yosys_template = self.get_template_path("yosys-script-nextpnr-xilinx-fasm2bels-tcl.j2")

        yosys_edam = {
                "files"         : self.files,
                "name"          : self.name,
                "toplevel"      : self.toplevel,
                "parameters"    : self.parameters,
                "tool_options"  : {
                                    "yosys" : {
                                        "arch" : vendor,
                                        "yosys_synth_options" : yosys_synth_options,
                                        "yosys_template" : yosys_template,
                                        "yosys_as_subtool" : True,
                                    }
                                }
                }

        yosys = getattr(import_module("edalize.yosys"), "Yosys")(yosys_edam, self.work_root)
        yosys.configure()

        # Nextpnr configuration
        package = self.tool_options.get("package")
        if not package:
            logger.error('Missing required "package" parameter')

        part = self.tool_options.get("part")
        if not part:
            logger.error('Missing required "part" parameter')

        target_family = None
        for family in getattr(self, "fpga_interchange_families"):
            if family in part:
                target_family = family
                break

        if target_family is None and arch is "fpga_interchange":
            logger.error("Couldn't find family for part: {}. Available families: {}".format(part, ", ".join(getattr(self, "fpga_interchange_families"))))

        chipdb = None
        device = None
        placement_constraints = []
        rr_graph = None
        vpr_grid = None
        vpr_capnp_schema = None

        for f in src_files:
            if f.file_type in ["bba"]:
                chipdb = f.name
            elif f.file_type in ["device"]:
                device = f.name
            elif f.file_type in ["xdc"]:
                placement_constraints.append(f.name)
            elif f.file_type in ["RRGraph"]:
                rr_graph = f.name
            elif f.file_type in ["VPRGrid"]:
                vpr_grid = f.name
            elif f.file_type in ["capnp"]:
                vpr_capnp_schema = f.name
            else:
                continue

        if not chipdb:
            logger.error("Missing required chipdb file")

        if placement_constraints == []:
            logger.error("Missing required XDC file(s)")

        if device is None and arch is "fpga_interchange":
            logger.error('Missing required ".device" file for "fpga_interchange" arch')

        nextpnr_options = self.tool_options.get("nextpnr_options", "")
        partname = part + package
        # Strip speedgrade string when using fpga_interchange
        package = package.split("-")[0] if arch == "fpga_interchange" else None

        if "xc7a" in part:
            bitstream_device = "artix7"
        if "xc7z" in part:
            bitstream_device = "zynq7"
        if "xc7k" in part:
            bitstream_device = "kintex7"

        nextpnr_makefile_name = self.name + "-nextpnr.mk"

        dbroot = self.tool_options.get("dbroot")
        clocks = self.tool_options.get("clocks")

        if fasm2bels:
            if any(v is None for v in [rr_graph, vpr_grid, dbroot]):
                logger.error("When using fasm2bels, rr_graph, vpr_grid and dbroot must be provided")

            tcl_params = {
                "top": self.name,
                "part": partname,
                "xdc": placement_constraints,
                "clocks": clocks,
            }

            self.render_template("symbiflow-fasm2bels-tcl.j2",
                                 "fasm2bels_vivado.tcl",
                                 tcl_params)

        makefile_params = {
            "top" : self.name,
            "partname" : partname,
            "bitstream_device" : bitstream_device,
            "fasm2bels": fasm2bels,
            "rr_graph": rr_graph,
            "vpr_grid": vpr_grid,
            "vpr_capnp_schema": vpr_capnp_schema,
            "dbroot": dbroot,
        }
        nextpnr_makefile_vars = {
                "toplevel"          : self.toplevel,
                "arch"              : arch,
                "chipdb"            : chipdb,
                "device"            : device,
                "constr"            : placement_constraints,
                "name"              : self.name,
                "package"           : package,
                "family"            : family,
                "additional_options": nextpnr_options,
        }

        self.render_template("symbiflow-nextpnr-{}-makefile.j2".format(arch),
                             "Makefile",
                             makefile_params)
        self.render_template("nextpnr-{}-makefile.j2".format(arch),
                             nextpnr_makefile_name,
                             nextpnr_makefile_vars)

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
        vpr_grid = None
        rr_graph = None
        vpr_capnp_schema = None

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
            if f.file_type in ["RRGraph"]:
                rr_graph = f.name
            if f.file_type in ["VPRGrid"]:
                vpr_grid = f.name
            if f.file_type in ["capnp"]:
                vpr_capnp_schema = f.name

        part = self.tool_options.get("part")
        package = self.tool_options.get("package")
        vendor = self.tool_options.get("vendor")

        if not part:
            logger.error('Missing required "part" parameter')
        if not package:
            logger.error('Missing required "package" parameter')

        if vendor == "xilinx":
            if "xc7a" in part:
                bitstream_device = "artix7"
            if "xc7z" in part:
                bitstream_device = "zynq7"
            if "xc7k" in part:
                bitstream_device = "kintex7"

            partname = part + package

            # a35t are in fact a50t
            # leave partname with 35 so we access correct DB
            if part == "xc7a35t":
                part = "xc7a50t"
            device_suffix = "test"
            toolchain_prefix = 'symbiflow_'
        elif vendor == "quicklogic":
            partname = package
            device_suffix = "wlcsp"
            bitstream_device = part + "_" + device_suffix
            toolchain_prefix = ""

        vpr_options = self.tool_options.get("vpr_options")

        fasm2bels = self.tool_options.get("fasm2bels", False)
        dbroot = self.tool_options.get("dbroot")
        clocks = self.tool_options.get("clocks")
        seed = self.tool_options.get("seed")

        if fasm2bels:
            if any(v is None for v in [rr_graph, vpr_grid, dbroot]):
                logger.error("When using fasm2bels, rr_graph, vpr_grid and database root must be provided")

            tcl_params = {
                "top": self.toplevel,
                "part": partname,
                "xdc": " ".join(placement_constraints),
                "clocks": clocks,
            }

            self.render_template("symbiflow-fasm2bels-tcl.j2",
                                 "fasm2bels_vivado.tcl",
                                 tcl_params)

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
            "fasm2bels": fasm2bels,
            "rr_graph": rr_graph,
            "vpr_grid": vpr_grid,
            "vpr_capnp_schema": vpr_capnp_schema,
            "dbroot": dbroot,
            "seed": seed,
            "device_suffix": device_suffix,
            "toolchain_prefix": toolchain_prefix,
            "vendor": vendor,
        }
        self.render_template("symbiflow-vpr-makefile.j2", "Makefile", makefile_params)

    def configure_main(self):
        if self.tool_options.get("pnr") == "nextpnr":
            self.configure_nextpnr()
        elif self.tool_options.get("pnr") in ["vtr", "vpr"]:
            self.configure_vpr()
        else:
            logger.error("Unsupported PnR tool: {}".format(self.tool_options.get("pnr")))

    def run_main(self):
        logger.info("Programming")
