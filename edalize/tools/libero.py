# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

from collections import defaultdict

from edalize.tools.edatool import Edatool
from edalize.utils import EdaCommands


class Libero(Edatool):
    """
    Microsemi Libero SoC backend.

    The Libero backend executes Libero to build systems and program the FPGA
    with FPExpress.
    """

    TOOL_OPTIONS = {
        "family": {
            "type": "str",
            "desc": "FPGA family (e.g. PolarFire)",
        },
        "die": {
            "type": "str",
            "desc": "FPGA device (e.g. MPF300TS)",
        },
        "package": {
            "type": "str",
            "desc": "FPGA package type (e.g. FCG1152)",
        },
        "speed": {
            "type": "str",
            "desc": "FPGA speed rating (e.g. -1)",
        },
        "dievoltage": {
            "type": "str",
            "desc": "FPGA die voltage (e.g. 1.0)",
        },
        "range": {
            "type": "str",
            "desc": "FPGA temperature range (e.g. IND)",
        },
        "defiostd": {
            "type": "str",
            "desc": 'FPGA default IO std (e.g. "LVCMOS 1.8V")',
        },
        "hdl": {
            "type": "str",
            "desc": 'Default HDL (e.g. "VERILOG")',
        },
    }

    argtypes = ["vlogdefine", "vlogparam", "generic"]
    mandatory_options = ["family", "die", "package", "range"]

    def setup(self, edam):
        super().setup(edam)
        incdirs = []
        src_files = []
        syn_files = []
        pnr_files = []
        tim_files = []
        iofile = None
        unused_files = []
        user_tcl_files = []
        io_state_file = []
        library_files = defaultdict(list)

        self.escaped_name = self.name.replace(".", "_")

        # Set default values
        tool_options = self.tool_options
        if "range" not in tool_options:
            tool_options["range"] = "IND"

        # Check mandatory options
        for key in self.mandatory_options:
            if key not in tool_options:
                raise RuntimeError(f'Libero option "{key}" must be defined')

        verilogFiles = 0
        VHDLFiles = 0

        for f in self.files:
            file_type = f.get("file_type", "")

            if file_type == "tclSource":
                user_tcl_files.append(f['name'])
                continue

            # Build source files that are part of libraries
            if "logical_name" in f.keys():
                library_files[f["logical_name"]].append(f['name'])

            if file_type.startswith("verilogSource"):
                verilogFiles += 1
                cmd = "-hdl_source"
            elif file_type.startswith("systemVerilogSource"):
                verilogFiles += 1
                cmd = "-hdl_source"
            elif file_type.startswith("vhdlSource"):
                VHDLFiles += 1
                cmd = "-hdl_source"
            elif file_type == "PDC":
                cmd = "-io_pdc"
            elif file_type == "SDC":
                cmd = "-sdc"
            elif file_type == "FPPDC":
                cmd = "-fp_pdc"
            elif file_type == "FDC":
                cmd = "-net_fdc"
            elif file_type == "NDC":
                cmd = "-ndc"
            else:
                unused_files.append(f)
                continue

            if not self._add_include_dir(f, incdirs, True):
                src_files.append(cmd + " {" + f["name"] + "}")

            # syn
            if file_type in ["FDC", "NDC", "SDC"]:
                syn_files.append("-file {" + f["name"] + "}")
            # pnr
            if file_type in ["FPPDC", "PDC", "SDC"]:
                pnr_files.append("-file {" + f["name"] + "}")
            # tim
            if file_type in ["SDC"]:
                tim_files.append("-file {" + f["name"] + "}")

            # io
            if file_type in ["IOS"]:
                iofile = f["name"]

        # Set preferred HDL language based on file type amount if not user defined.
        # According to docs, projects can be mixed but one language must be
        # defined as preferred
        self.tool_options["hdl"] = "VERILOG" if verilogFiles > VHDLFiles else "VHDL"

        self.edam = edam.copy()
        self.edam["files"] = unused_files

        self.template_vars = {
            "name": self.escaped_name,
            "toplevel": self.toplevel,
            "prj_root": "./prj",
            "src_files": src_files,
            "syn_files": syn_files,
            "pnr_files": pnr_files,
            "tim_files": tim_files,
            "iofile": iofile,
            "user_tcl_files": user_tcl_files,
            "library_files": library_files,
            "incdirs": incdirs + ["."],
            "vlogparam": self.vlogparam,
            "vlogdefine": self.vlogdefine,
            "generic": self.generic,
            "tool_options": self.tool_options,
            "op": "{",
            "cl": "}",
            "sp": " ",
        }

        commands = EdaCommands()

        script_project = self.escaped_name + "-project.tcl"
        prjx_file = self.escaped_name + ".prjx"

        script_build = self.escaped_name + "-build.tcl"
        job_file = self.escaped_name + ".job"
        script_pgm = self.escaped_name + "-pgm.tcl"

        commands.add(
            command=["libero", f"SCRIPT:{script_project}"],
            targets=[prjx_file],
            depends=[],
        )
        commands.add(
            command=["libero", f"SCRIPT:{script_build}"],
            targets=[job_file],
            depends=[prjx_file],
        )

        commands.add(
            command=["FPExpress", f"SCRIPT:{script_pgm}"],
            targets=["pgm"],
            depends=[script_pgm, job_file],
        )

        commands.set_default_target(job_file)
        self.commands = commands

    def write_config_files(self):
        self.render_template(
            "libero-project.tcl.j2", self.escaped_name + "-project.tcl", self.template_vars,
        )

        self.render_template(
            "libero-syn-user.tcl.j2", self.escaped_name + "-syn-user.tcl", self.template_vars,
        )

        self.render_template(
            "libero-build.tcl.j2", self.escaped_name + "-build.tcl", self.template_vars,
        )

        self.render_template(
            "libero-pgm.tcl.j2", self.escaped_name + "-pgm.tcl", self.template_vars,
        )

    def run(self):
        """
        Program the FPGA.
        """
        return ("make", ["pgm"], self.work_root)
