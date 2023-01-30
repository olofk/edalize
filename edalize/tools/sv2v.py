from edalize.tools.edatool import Edatool
from edalize.utils import EdaCommands


class Sv2v(Edatool):

    description = "SystemVerilog to Verilog conversion"

    TOOL_OPTIONS = {
        "sv2v_options": {
            "type": "str",
            "desc": "Additional options for sv2v",
            "list": True,
        },
    }

    def setup(self, edam):
        super().setup(edam)

        incdirs = []
        sv_files = []
        unused_files = []

        for f in self.files:
            if f.get("file_type").startswith("systemVerilogSource"):
                if not self._add_include_dir(f, incdirs):
                    sv_files.append(f["name"])
            else:
                unused_files.append(f)

        output_file = self.name + ".v"
        self.edam = edam.copy()
        self.edam["files"] = unused_files
        self.edam["files"].append(
            {
                "name": output_file,
                "file_type": "verilogSource",
            }
        )

        sv2v_options = self.tool_options.get("sv2v_options", [])

        commands = EdaCommands()
        commands.add(
            ["sv2v", "-w", output_file]
            + sv2v_options
            + ["-I" + d for d in incdirs]
            + sv_files,
            [output_file],
            sv_files,
        )

        commands.set_default_target(output_file)
        self.commands = commands
