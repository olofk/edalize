from edalize.tools.edatool import Edatool
from edalize.utils import EdaCommands


class Flist(Edatool):

    description = "F-list generator"

    TOOL_OPTIONS = {}

    def setup(self, edam):
        super().setup(edam)

        self.f = []

        for key, value in self.vlogdefine.items():
            define_str = self._param_value_str(param_value=value)
            self.f.append(f"+define+{key}={define_str}")

        for key, value in self.vlogparam.items():
            param_str = self._param_value_str(param_value=value, str_quote_style='"')
            self.f.append(f"-pvalue+{self.toplevel}.{key}={param_str}")

        incdirs = []
        vlog_files = []
        depfiles = []
        unused_files = []

        for f in self.files:
            file_type = f.get("file_type", "")
            depfile = True
            if file_type.startswith("systemVerilogSource") or file_type.startswith(
                "verilogSource"
            ):
                if not self._add_include_dir(f, incdirs):
                    vlog_files.append(f["name"])
            else:
                unused_files.append(f)
                depfile = False

            if depfile:
                depfiles.append(f["name"])

        for include_dir in incdirs:
            self.f.append(f"+incdir+{include_dir}")

        for vlog_file in vlog_files:
            self.f.append(f"{vlog_file}")

        self.edam = edam.copy()
        self.edam["files"] = unused_files

        output_file = self.name + ".f"
        self.edam = edam.copy()
        self.edam["files"] = unused_files
        self.edam["files"].append(
            {
                "name": output_file,
                "file_type": "verilogSource",
            }
        )

        commands = EdaCommands()
        commands.add(
            [],
            [output_file],
            depfiles,
        )

        commands.set_default_target(output_file)
        self.commands = commands

    def write_config_files(self):
        self.update_config_file(self.name + ".f", "\n".join(self.f) + "\n")
