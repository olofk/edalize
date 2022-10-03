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
        # Optional, defaults to VPR
        "pnr": {
            "type": "str",
            "desc": "Place and route tool. Valid options are 'vpr'/'vtr' and 'nextpnr'. Defaults to VPR.",
        }
    }

    # Define which tools are called and in what order
    def configure_flow(self, flow_options):
        flow = ["yosys"]
        if flow_options.get("pnr") in ["nextpnr"]:
            flow += ["nextpnr"]
        else:
            flow += ["vpr"]
        return flow
