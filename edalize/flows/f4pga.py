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

        # Set up nodes
        synth_tool = "yosys"
        pnr_tool = ""
        if "pnr" in flow_options and flow_options.get("pnr") in ["nextpnr"]:
            pnr_tool = "nextpnr"
        else:
            pnr_tool = "vpr"

        in_xdc = "IN_XDC"
        part_json = "PART_JSON"

        # Set up node options
        synth_options = {}
        if "arch" in flow_options:
            synth_options.update({"arch": flow_options.get("arch")})
        else:
            synth_options.update({"arch": "xilinx"})
        synth_options.update(
            {"output_format": "eblif"}
        )  # <- Make this variable because NextPNR wants a JSON
        synth_options.update({"yosys_template": "$(python3 -m f4pga.wrappers.tcl)"})
        synth_options.update({"f4pga_synth": [in_xdc, part_json]})

        pnr_options = {}
        if pnr_tool == "vpr":
            arch_xml = "ARCH_XML"
            pnr_options.update({"arch_xml": arch_xml})
            pnr_options.update({"gen_constraints": []})
        elif pnr_tool == "nextpnr":
            pnr_options.update({"arch": flow_options.get("arch")})

        # Set target
        toplevel = self.edam["toplevel"]
        self.commands.set_default_target(f"{toplevel}.bit")

        return [(synth_tool, [pnr_tool], synth_options), (pnr_tool, [], pnr_options)]
