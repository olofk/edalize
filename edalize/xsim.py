# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import os
import logging

from collections import OrderedDict
from edalize.edatool import Edatool

logger = logging.getLogger(__name__)


class Xsim(Edatool):

    argtypes = ["plusarg", "vlogdefine", "vlogparam", "generic"]

    MAKEFILE_TEMPLATE = """#Auto generated by Edalize
include config.mk

all: xsim.dir/$(TARGET)/xsimk

xsim.dir/$(TARGET)/xsimk:
	xelab $(TOPLEVEL) -prj $(TARGET).prj -snapshot $(TARGET) $(VLOG_DEFINES) $(VLOG_INCLUDES) $(GEN_PARAMS) $(XELAB_OPTIONS)

run: xsim.dir/$(TARGET)/xsimk
	xsim -R $(XSIM_OPTIONS) $(TARGET) $(EXTRA_OPTIONS)

run-gui: xsim.dir/$(TARGET)/xsimk
	xsim --gui $(XSIM_OPTIONS) $(TARGET) $(EXTRA_OPTIONS)
"""

    CONFIG_MK_TEMPLATE = """#Auto generated by Edalize
TARGET        = {target}
TOPLEVEL      = {toplevel}

VLOG_DEFINES  = {vlog_defines}
VLOG_INCLUDES = {vlog_includes}
GEN_PARAMS    = {gen_params}

XELAB_OPTIONS =	{xelab_options}
XSIM_OPTIONS  = {xsim_options}
"""

    @classmethod
    def get_doc(cls, api_ver):
        if api_ver == 0:
            return {
                "description": "XSim simulator from the Xilinx Vivado suite",
                "members": [
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
                else:
                    _s = "{} has unknown file type '{}'"
                    logger.warning(_s.format(src_file.name, src_file.file_type))
                if cmd:
                    if src_file.logical_name:
                        lib = src_file.logical_name
                    else:
                        lib = "work"
                    f.write("{} {} {}\n".format(cmd, lib, src_file.name))
            if mfc:
                f.write("sv work " + " ".join(mfcu))

        with open(os.path.join(self.work_root, "config.mk"), "w") as f:
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

            f.write(
                self.CONFIG_MK_TEMPLATE.format(
                    target=self.name,
                    toplevel=self.toplevel,
                    vlog_defines=vlog_defines,
                    vlog_includes=vlog_includes,
                    gen_params=gen_param_args,
                    xelab_options=xelab_options,
                    xsim_options=xsim_options,
                )
            )

        with open(os.path.join(self.work_root, "Makefile"), "w") as f:
            f.write(self.MAKEFILE_TEMPLATE)

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
