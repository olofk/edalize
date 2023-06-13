import os
from edalize.tools.edatool import Edatool
from edalize.utils import EdaCommands


class Customtool(Edatool):

    description = "Custom tool"

    TOOL_OPTIONS = {
        "custom_tool_options": {
            "type": "str",
            "desc": "Additional options for custom tool",
            "list": True,
        },
    }

    def setup(self, edam):
        super().setup(edam)

        used_files = []
        unused_files = []

        for f in self.files:
            # This custom tool only operates on files with file names
            # that have an odd length
            if len(f["name"]) % 2:
                used_files.append(f["name"])
            else:
                unused_files.append(f)
        # f"{f['name']} is a {f.get('file_type')} file")

        # Copy the input EDAM and replace the files with the list
        # of unused files + the files that this tool creates
        output_file = self.name + ".count"
        self.edam = edam.copy()
        self.edam["files"] = unused_files
        self.edam["files"].append(
            {
                "name": output_file,
                "file_type": "some_kind_of_file",
            }
        )

        # Define a configuration file to be written
        self.config_file = self.name + ".cfg"

        # Define the command(s) to run the actual EDA tool
        # This example just uses wc to count the number of
        # charactes, words and lines of the source files
        # and writes the results to a file
        commands = EdaCommands()
        commands.add(
            ["wc"]
            + self.tool_options.get("custom_tool_options", [])
            + used_files
            + [self.config_file, ">", output_file],
            [output_file],
            used_files,
        )

        # Define the default output product of this tool
        commands.set_default_target(output_file)
        self.commands = commands

    def write_config_files(self):
        with open(
            os.path.join(
                self.work_root,
                self.config_file,
            ),
            "w",
        ) as cfg_file:
            cfg_file.write("This is a config file for custom tool\n")
