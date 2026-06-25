# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

from __future__ import annotations

import os.path
from typing import Any

from edalize.flows.edaflow import Edaflow, FlowGraph, FlowNodeSpec


class Vpr(Edaflow):
    """VPR is an open source academic CAD tool designed for the exploration of new FPGA architectures and CAD algorithms, at the packing, placement and routing phases of the CAD flow"""

    argtypes = ["vlogdefine", "vlogparam"]

    def configure_flow(self, flow_options: dict[str, Any]) -> FlowGraph:

        flow: dict[str, FlowNodeSpec] = {
            "yosys": {"fdto": {"output_format": "blif"}},
            "vpr": {"deps": ["yosys"]},
        }
        return FlowGraph.fromdict(flow)

    def configure_tools(self, nodes: FlowGraph) -> None:
        super().configure_tools(nodes)
        name = self.edam["name"]
        self.commands.set_default_target(name + ".analysis")
