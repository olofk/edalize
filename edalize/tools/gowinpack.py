# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

from edalize.tools.edatool import Edatool
from edalize.utils import EdaCommands


class Gowinpack(Edatool):

    description = "Generate binary image for Gowin FPGAs"

    TOOL_OPTIONS = {
        "gowin_pack_options": {
            "type": "str",
            "desc": "Additional options for gowin_pack",
            "list": True,
        },
        "device": {
            "type": "str",
            "desc": "FPGA device code (e.g. GW1N-LV1QN48C6/I5)",
        },
        "device_family": {
            "type": "str",
            "desc": "FPGA device family (e.g. GW1N-9C)",
        },
    }

    def setup(self, edam):
        super().setup(edam)

        unused_files = []
        # First try the device family, then the device
        device = self.tool_options.get("device_family", "")
        if not device:
            device = self.tool_options.get("device", "")
        if not device:
            raise RuntimeError("No device or device family specified")

        routed_json_file = ""
        bin_file = ""
        for f in self.files:
            if f.get("file_type") == "nextpnrRoutedJson":
                if routed_json_file:
                    raise RuntimeError(
                        "gowin_pack only supports one input file. Found {} and {}".format(
                            routed_json_file, f["name"]
                        )
                    )
                routed_json_file = f["name"]
            else:
                unused_files.append(f)

        if not routed_json_file:
            raise RuntimeError("No input file specified for gowin_pack")

        fs_file = self.edam["name"] + ".fs"
        self.edam = edam.copy()
        self.edam["files"] = unused_files
        self.edam["files"].append({"name": fs_file, "file_type": "gowinFusesFile"})

        # Image generation
        depends = routed_json_file
        targets = fs_file
        command = (
            ["gowin_pack", "-d", device, "-o", targets]
            + self.tool_options.get("gowin_pack_options", [])
            + [depends]
        )

        commands = EdaCommands()
        commands.add(command, [targets], [depends])
        commands.set_default_target(targets)
        self.commands = commands
