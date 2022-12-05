# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import os.path

from edalize.flows.edaflow import Edaflow


class Vivado(Edaflow):
    """The Vivado backend executes Xilinx Vivado to build systems and program the FPGA"""

    argtypes = ["vlogdefine", "vlogparam"]

    FLOW_DEFINED_TOOL_OPTIONS = {
        "yosys": {"arch": "xilinx", "output_format": "edif"},
    }

    FLOW_OPTIONS = {
        "frontends": {
            "type": "str",
            "desc": "Tools to run before yosys (e.g. sv2v)",
            "list": True,
        },
        "pnr": {
            "type": "str",
            "desc": "Select Place & Route tool.",
        },
        "synth": {
            "type": "str",
            "desc": "Synthesis tool. Allowed values are vivado (default) and yosys.",
        },
    }

    @classmethod
    def get_tool_options(cls, flow_options):
        flow = flow_options.get("frontends", [])

        if flow_options.get("synth") == "yosys":
            flow.append("yosys")
        flow.append("vivado")

        return cls.get_filtered_tool_options(flow, cls.FLOW_DEFINED_TOOL_OPTIONS)

    def configure_flow(self, flow_options):
        flow = []
        if flow_options.get("synth") == "yosys":
            flow = [
                ("yosys", ["vivado"], self.FLOW_DEFINED_TOOL_OPTIONS["yosys"]),
                ("vivado", [], {"synth": "yosys"}),
            ]
            next_tool = "yosys"
        else:
            flow = [("vivado", [], {})]
            next_tool = "vivado"

        # Add any user-specified frontends to the flow
        for frontend in reversed(flow_options.get("frontends", [])):
            flow[0:0] = [(frontend, [next_tool], {})]
            next_tool = frontend
        return flow

    def configure_tools(self, nodes):
        super().configure_tools(nodes)
        name = self.edam["name"]
        self.commands.set_default_target(name + ".bit")
