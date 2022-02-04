# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import os.path

from edalize.flows.edaflow import Edaflow


class Vpr(Edaflow):
    """VPR is an open source academic CAD tool designed for the exploration of new FPGA architectures and CAD algorithms, at the packing, placement and routing phases of the CAD flow"""

    argtypes = ["vlogdefine", "vlogparam"]

    FLOW = [
        ("yosys", ["vpr"], {"output_format": "blif"}),
        ("vpr", [], {}),
    ]

    FLOW_OPTIONS = {}

    def build_tool_graph(self):
        return super().build_tool_graph()

    def configure_tools(self, nodes):
        super().configure_tools(nodes)
        name = self.edam["name"]
        self.commands.set_default_target(name + ".analysis")
