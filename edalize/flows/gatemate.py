# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import os.path

from edalize.flows.edaflow import Edaflow, FlowGraph

class Gatemate(Edaflow):
    """Open source toolchain for Cologne Chip GateMate FPGAs. Uses yosys for synthesis and nextpnr for Place & Route"""

    argtypes = ["vlogdefine", "vlogparam"]

    _flow = {
        "yosys": {"fdto": {"arch": "gatemate", "output_format": "json",
                           "yosys_synth_options": ["-luttree", "-nomx8"],
                           }},
        "nextpnr": {"deps": ["yosys"],
                    "fdto": {"arch": "gatemate",
                             "nextpnr_options": ["--router router2"],
                             }},
        "gmpack": {"deps": ["nextpnr"]},
    }

    @classmethod
    def get_tool_options(cls, flow_options):
        tools = flow_options.get("frontends", []) + list(cls._flow)

        flow_defined_tool_options = {}
        for k, v in cls._flow.items():
            flow_defined_tool_options[k] = v.get("fdto", {})
        return cls.get_filtered_tool_options(tools, flow_defined_tool_options)

    def configure_flow(self, flow_options):

        flow = self._flow.copy()

        # Add any user-specified frontends to the flow
        deps = []
        for frontend in flow_options.get("frontends", []):
            flow[frontend] = {"deps": deps}
            deps = [frontend]

        flow["yosys"]["deps"] = deps

        name = self.edam["name"]
        self.commands.add([], ["synth"], [name + ".json"])
        self.commands.add([], ["bitstream"], [name + ".bit"])
        self.commands.set_default_target("bitstream")

        return FlowGraph.fromdict(flow)
