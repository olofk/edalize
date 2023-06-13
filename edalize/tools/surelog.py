import os.path

from edalize.tools.edatool import Edatool
from edalize.utils import EdaCommands


class Surelog(Edatool):

    description = "SystemVerilog 2017 Pre-processor, Parser, Elaborator, UHDM Compiler"

    TOOL_OPTIONS = {
        "surelog_options": {
            "type": "str",
            "desc": "Additional options for surelog",
            "list": True,
        },
    }

    def setup(self, edam):
        super().setup(edam)

        incdirs = []
        file_table = []
        unused_files = []

        depfiles = []

        # Filter out input files
        for f in self.files:
            src = ""
            if "file_type" in f:
                file_type = f.get("file_type", "")
                if file_type.startswith("verilogSource"):
                    src = f["name"]
                elif file_type.startswith("systemVerilogSource"):
                    src = "-sv " + f["name"]

                if src:
                    depfiles.append(f["name"])
                    if not self._add_include_dir(f, incdirs):
                        file_table.append(src)
                else:
                    unused_files.append(f)

        # Create output EDAM
        output_file = "slpp_all/surelog.uhdm"
        self.edam = edam.copy()
        self.edam["files"] = unused_files
        self.edam["files"].append({"name": output_file, "file_type": "uhdm"})

        # Handle verilog defines
        verilog_defines = []
        for key, value in self.vlogdefine.items():
            verilog_params.append(f"+define+{key}={value}")

        # Handle verilog parameters
        verilog_params = []
        for key, value in self.vlogparam.items():
            verilog_params.append(f"-P{key}={value}")

        commands = EdaCommands()

        commands.add(
            ["surelog", "-top", self.toplevel]
            + self.tool_options.get("surelog_options", [])
            + ["-parse"]
            + verilog_defines
            + verilog_params
            + ["-I" + d for d in incdirs]
            + file_table,
            [output_file],
            depfiles,
        )

        commands.set_default_target(output_file)
        self.commands = commands
