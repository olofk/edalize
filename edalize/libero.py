import logging
import os
import shutil
from pathlib import Path
from collections import defaultdict
from edalize.edatool import Edatool
from edalize.utils import get_file_type

logger = logging.getLogger(__name__)


class Libero(Edatool):
    @classmethod
    def get_doc(cls, api_ver):
        if api_ver == 0:
            return {
                "description": "The Libero backend supports Microsemi Libero to build systems and program the FPGA",
                "members": [
                    {
                        "name": "family",
                        "type": "String",
                        "desc": "FPGA family (e.g. PolarFire)",
                    },
                    {
                        "name": "die",
                        "type": "String",
                        "desc": "FPGA device (e.g. MPF300TS)",
                    },
                    {
                        "name": "package",
                        "type": "String",
                        "desc": "FPGA package type (e.g. FCG1152)",
                    },
                    {
                        "name": "speed",
                        "type": "String",
                        "desc": "FPGA speed rating (e.g. -1)",
                    },
                    {
                        "name": "dievoltage",
                        "type": "String",
                        "desc": "FPGA die voltage (e.g. 1.0)",
                    },
                    {
                        "name": "range",
                        "type": "String",
                        "desc": "FPGA temperature range (e.g. IND)",
                    },
                    {
                        "name": "defiostd",
                        "type": "String",
                        "desc": 'FPGA default IO std (e.g. "LVCMOS 1.8V")',
                    },
                    {
                        "name": "hdl",
                        "type": "String",
                        "desc": 'Default HDL (e.g. "VERILOG")',
                    },
                ],
            }

    argtypes = ["vlogdefine", "vlogparam", "generic"]
    mandatory_options = ["family", "die", "package", "range"]

    tool_options_defaults = {
        "range": "IND",
    }

    def _set_tool_options_defaults(self):
        for key, default_value in self.tool_options_defaults.items():
            if not key in self.tool_options:
                logger.info(
                    "Set Libero tool option %s to default value %s"
                    % (key, str(default_value))
                )
                self.tool_options[key] = default_value

    def _check_mandatory_options(self):
        shouldExit = 0
        for key in self.mandatory_options:
            if not key in self.tool_options:
                logger.error('Libero option "%s" must be defined', key)
                shouldExit = 1
        if shouldExit:
            raise RuntimeError("Missing required tool options")

    def configure_main(self):
        """
        Configuration is the first phase of the build.

        This writes the project TCL file. It first collects all
        sources, IPs and constraints and then writes them to the TCL file along
        with the build steps.
        """
        self._set_tool_options_defaults()
        self._check_mandatory_options()
        (src_files, incdirs) = self._get_fileset_files(force_slash=True)
        self.jinja_env.filters["src_file_filter"] = self.src_file_filter
        self.jinja_env.filters[
            "syn_constraint_file_filter"
        ] = self.syn_constraint_file_filter
        self.jinja_env.filters[
            "pnr_constraint_file_filter"
        ] = self.pnr_constraint_file_filter
        self.jinja_env.filters[
            "tim_constraint_file_filter"
        ] = self.tim_constraint_file_filter
        self.jinja_env.filters["tcl_file_filter"] = self.tcl_file_filter

        escaped_name = self.name.replace(".", "_")

        # Add Edalize working dir to Synthesys includes removing duplicates
        incdirs = list(set(incdirs.__add__(["."])))

        # Build source files that are part of libraries
        library_files = defaultdict(list)
        for f in src_files:
            if f.logical_name:
                library_files[f.logical_name].append(f.name)

        template_vars = {
            "name": escaped_name,
            "src_files": src_files,
            "library_files": library_files,
            "incdirs": incdirs,
            "vlogparam": self.vlogparam,
            "vlogdefine": self.vlogdefine,
            "generic": self.generic,
            "tool_options": self.tool_options,
            "toplevel": self.toplevel,
            "generic": self.generic,
            "prj_root": "./prj",
            "op": "{",
            "cl": "}",
            "sp": " ",
        }

        # Set preferred HDL language based on file type amount if not user defined.
        # According to docs, projects can be mixed but one language must be
        # defined as preferred
        if not "hdl" in self.tool_options:
            verilogFiles = 0
            VHDLFiles = 0
            for f in src_files:
                t = get_file_type(f)
                if t == "verilogSource" or t == "systemVerilogSource":
                    verilogFiles += 1
                elif t == "vhdlSource":
                    VHDLFiles += 1
            if verilogFiles >= VHDLFiles:
                self.tool_options["hdl"] = "VERILOG"
            else:
                self.tool_options["hdl"] = "VHDL"

        # Render the TCL project file
        self.render_template(
            "libero-project.tcl.j2", escaped_name + "-project.tcl", template_vars
        )

        # Render the TCL run file
        self.render_template(
            "libero-run.tcl.j2", escaped_name + "-run.tcl", template_vars
        )

        # Render the Synthesize TCL file
        self.render_template(
            "libero-syn-user.tcl.j2", escaped_name + "-syn-user.tcl", template_vars
        )

        logger.info("Cores and Libero TCL Scripts generated.")

    def src_file_filter(self, f):
        file_types = {
            "verilogSource": "-hdl_source {",
            "systemVerilogSource": "-hdl_source {",
            "vhdlSource": "-hdl_source {",
            "PDC": "-io_pdc {",
            "SDC": "-sdc {",
            "FPPDC": "-fp_pdc {",
            "FDC": "-net_fdc {",
            "NDC": "-ndc {",
        }
        _file_type = get_file_type(f)
        if _file_type in file_types:
            # Do not return library files here
            if f.logical_name:
                return ""
            return file_types[_file_type] + f.name
        return ""

    def tcl_file_filter(self, f):
        file_types = {
            "tclSource": "source ",
        }
        _file_type = get_file_type(f)
        if _file_type in file_types:
            return file_types[_file_type] + f.name
        return ""

    def syn_constraint_file_filter(self, f):
        if f.file_type in ["FDC", "NDC", "SDC"]:
            return f.name

    def pnr_constraint_file_filter(self, f):
        if f.file_type in ["FPPDC", "PDC", "SDC"]:
            return f.name

    def tim_constraint_file_filter(self, f):
        if f.file_type == "SDC":
            return f.name

    def build_main(self):
        logger.info("Executing Libero TCL Scripts.")
        escaped_name = self.name.replace(".", "_")
        if shutil.which("libero"):
            self._run_tool("libero", ["SCRIPT:" + escaped_name + "-run.tcl"])
        else:
            filePath = os.path.join(
                Path(self.work_root).relative_to(os.getcwd()), escaped_name + "-run.tcl"
            )
            logger.warn(
                'Libero not found on path, execute manually the script "'
                + filePath
                + '"'
            )

    def run_main(self):
        pass
