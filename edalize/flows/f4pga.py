# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import os.path

from edalize.flows.edaflow import Edaflow


class F4pga(Edaflow):
    """Edalize back-end implementation of F4PGA (Free and Open-Source Flow For FPGAs)"""

    """Currently supports Xilinx 7-series chips"""

    # F4PGA defined inputs to the underlying tools
    FLOW_DEFINED_TOOL_OPTIONS = {}

    # Inputs to the F4PGA flow
    FLOW_OPTIONS = {
        # Required
        "device": {"type": "str", "desc": "Example: 'artix7'"},
        # Required
        "part": {"type": "str", "desc": "Example: 'xc7a35tcpg236-1'"},
        # Optional, defaults to xilinx
        "arch": {
            "type": "str",
            "desc": "Targeting architecture for Yosys. Currently supported is 'xilinx' and that is the default if none specified.",
        },
        # Optional, defaults to VPR
        "pnr": {
            "type": "str",
            "desc": "Place and route tool. Valid options are 'vpr'/'vtr' and 'nextpnr'. Defaults to VPR.",
        },
    }

    # Define which tools are called and in what order
    def configure_flow(self, flow_options):

        # Set target
        # toplevel = self.edam["toplevel"]
        name = self.edam["name"]
        self.commands.set_default_target(f"{name}.bit")

        # Set up nodes
        synth_tool = "yosys"
        pnr_tool = ""
        if "pnr" in flow_options and flow_options.get("pnr") in ["nextpnr"]:
            pnr_tool = "nextpnr"
        else:
            pnr_tool = "vpr"

        device = flow_options.get("device")
        if not device:
            print("F4PGA flow error: missing 'device' specifier")
            return []

        part = flow_options.get("part")
        if not part:
            print("F4PGA flow error: missing 'part' specifier")
            return []

        part_json = f"$(shell prjxray-config)/{device}/{part}/part.json"

        # Set up node options
        synth_options = {}
        if "arch" in flow_options:
            synth_options.update({"arch": flow_options.get("arch")})
        else:
            synth_options.update({"arch": "xilinx"})
        synth_options.update(
            {"output_format": "eblif"}
        )  # <- Make this variable because NextPNR wants a JSON
        synth_options.update(
            {"yosys_template": "$(shell python3 -m f4pga.wrappers.tcl)"}
        )
        synth_options.update({"f4pga_synth_part_file": part_json})

        pnr_options = {}
        if pnr_tool == "vpr":
            arch_xml = "ARCH_XML"
            pnr_options.update({"arch_xml": arch_xml})
            pnr_options.update({"gen_constraints": []})
        elif pnr_tool == "nextpnr":
            pnr_options.update({"arch": flow_options.get("arch")})

        return [(synth_tool, [pnr_tool], synth_options), (pnr_tool, [], pnr_options)]
