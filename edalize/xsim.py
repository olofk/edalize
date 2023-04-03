# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import os
import logging

from collections import OrderedDict
from edalize.edatool import Edatool

logger = logging.getLogger(__name__)


class Xsim(Edatool):
    """ 
    Vivado Xsim backend
    * Standard design sources
    * IP: Supply the IP core xci file with file_type=xci and other files (like .prj) as file_type=user . 
      you also have to specify xilinx part number in tools/xsim/part

    * you can also set tools/xsim/default_run to "run_vcd" in order to automatically generate vcd file during simulation
    """

    argtypes = ["plusarg", "vlogdefine", "vlogparam", "generic"]


    VCD_TCL = """#tcl script that runs simulation with vcd output
open_vcd xsim_dump.vcd
log_vcd *
run all
close_vcd
quit
"""
    @classmethod
    def get_doc(cls, api_ver):
        if api_ver == 0:
            return {
                "description": "XSim simulator from the Xilinx Vivado suite",
                "members": [
                    {
                        "name": "part",
                        "type": "String",
                        "desc": "xilinx part if using xci ip",
                    },
                    {
                        "name": "default_run",
                        "type": "String",
                        "desc": "default target to run for makefile. use 'run-vcd' for automatic vcd generation",
                    },
                    {
                        "name": "compilation_mode",
                        "type": "String",
                        "desc": "Common or separate compilation, sep - for separate compilation, common - for common compilation",
                    }
                ],
                "lists": [
                    {
                        "name": "xelab_options",
                        "type": "String",
                        "desc": "Additional options for compilation with xelab",
                    },
                    {
                        "name": "xsim_options",
                        "type": "String",
                        "desc": "Additional run options for XSim",
                    },
                ],
            }

    def configure_main(self):
        self._write_config_files()

        # Check if any VPI modules are present and display warning
        if len(self.vpi_modules) > 0:
            modules = [m["name"] for m in self.vpi_modules]
            logger.error("VPI modules not supported by Xsim: %s" % ", ".join(modules))

    def _write_config_files(self):
        mfc = self.tool_options.get("compilation_mode") == "common"
        with open(os.path.join(self.work_root, self.name + ".prj"), "w") as f:
            mfcu = []
            (src_files, self.incdirs) = self._get_fileset_files()
            src_list = []
            xci_list = []
            for src_file in src_files:
                cmd = ""
                if src_file.file_type.startswith("verilogSource"):
                    cmd = "verilog"
                elif src_file.file_type == "vhdlSource-2008":
                    cmd = "vhdl2008"
                elif src_file.file_type.startswith("vhdlSource"):
                    cmd = "vhdl"
                elif src_file.file_type.startswith("systemVerilogSource"):
                    if mfc:
                        mfcu.append(src_file.name)
                    else:
                        cmd = "sv"
                elif src_file.file_type in ["user"]:
                    pass
                elif src_file.file_type in ["data"]:
                    os.system("ln -s %s %s"%(src_file.name, os.path.join(self.work_root, os.path.basename(src_file.name))));
                elif src_file.file_type in ["xci"]:
                    xci_list.append(src_file.name)
                else:
                    _s = "{} has unknown file type '{}'"
                    logger.warning(_s.format(src_file.name, src_file.file_type))
                if cmd:
                    src_list.append(src_file.name)
                    if src_file.logical_name:
                        lib = src_file.logical_name
                    else:
                        lib = "work"
                    f.write("{} {} {}\n".format(cmd, lib, src_file.name))
            if mfc:
                f.write("sv work " + " ".join(mfcu))

        if 1:
            vlog_defines = " ".join(
                [
                    "--define {}={}".format(k, self._param_value_str(v))
                    for k, v, in self.vlogdefine.items()
                ]
            )
            vlog_includes = " ".join(["-i " + k for k in self.incdirs])

            # Both parameters and generics use the same --generic_top argument
            # so warn if there are overlapping values
            common_vals = set(self.vlogparam).intersection(set(self.generic))
            if common_vals != set():
                _s = "Common values for vlogparam and generic: {}"
                logger.warning(_s.format(common_vals))

            gen_param = OrderedDict(self.vlogparam)
            gen_param.update(self.generic)
            gen_param_args = " ".join(
                [
                    '--generic_top "{}={}"'.format(k, self._param_value_str(v))
                    for k, v in gen_param.items()
                ]
            )
            xelab_options = " ".join(self.tool_options.get("xelab_options", []))
            xsim_options = " ".join(self.tool_options.get("xsim_options", []))

            if xci_list:
                xci_part = self.tool_options.get("part", "dflt_part")
                if xci_part == "dflt_part":
                    logger.error("When using xci, you must define tools/xsim/part value")
                self.render_template("xci.tcl.j2", os.path.join(self.work_root, "xci.tcl"), dict(
                    xci_list = xci_list,
                    xci_part = xci_part
                ))
            self.render_template("config.mk.j2", os.path.join(self.work_root, "config.mk"), dict(
                    target=self.name,
                    toplevel=self.toplevel,
                    vlog_defines=vlog_defines,
                    vlog_includes=vlog_includes,
                    gen_params=gen_param_args,
                    xelab_options=xelab_options,
                    xsim_options=xsim_options,
                    src_list=src_list,
            ))

        self.render_template("Makefile.j2",os.path.join(self.work_root, "Makefile"),dict(
            default_run = self.tool_options.get("default_run", "run-dflt"),
            xci_list = xci_list
        ))
        with open(os.path.join(self.work_root, "vcd.tcl"), "w") as f:
            f.write(self.VCD_TCL)

    def run_main(self):
        args = ["run"]
        # Plusargs
        if self.plusarg:
            _s = "--testplusarg {}={}"
            args.append(
                "EXTRA_OPTIONS="
                + " ".join([_s.format(k, v) for k, v in self.plusarg.items()])
            )

        self._run_tool("make", args)
