# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import os.path

from edalize.flows.edaflow import Edaflow, FlowGraph


class Vivado(Edaflow):
    """The Vivado flow executes AMD Vivado to create a bitstream and optionally program a board. Yosys can be used for synthesis by setting the synth option accordingly"""

    argtypes = ["vlogdefine", "vlogparam"]

    FLOW_DEFINED_TOOL_OPTIONS = {
        "yosys": {"arch": "xilinx", "output_format": "edif"},
    }

    FLOW_OPTIONS = {
        "frontends": {
            "type": "str",
            "desc": "Tools to run before Vivado (e.g. sv2v)",
            "list": True,
        },
        "pgm": {
            "type": "bool",
            "desc": "Program board after bitstream is complete",
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
        flow = flow_options.get("frontends", []).copy()

        if flow_options.get("synth") == "yosys":
            flow.append("yosys")
        flow.append("vivado")

        return cls.get_filtered_tool_options(flow, cls.FLOW_DEFINED_TOOL_OPTIONS)

    def configure_flow(self, flow_options):
        flow = {}

        # Add any user-specified frontends to the flow
        deps = []
        for frontend in flow_options.get("frontends", []):
            flow[frontend] = {"deps": deps}
            deps = [frontend]

        if flow_options.get("synth") == "yosys":
            flow["yosys"] = {
                "deps": deps,
                "fdto": self.FLOW_DEFINED_TOOL_OPTIONS["yosys"],
            }
            flow["vivado"] = {"deps": ["yosys"], "fdto": {"synth": "none"}}
        else:
            flow["vivado"] = {"deps": deps}

        name = self.edam["name"]
        self.commands.set_default_target(name + ".bit")
        return FlowGraph.fromdict(flow)

    def run(self):
        if self.flow_options.get("pgm"):

            # Get run command from tool instance
            vivado_inst = self.flow.get_node("vivado").inst
            (cmd, args, cwd) = vivado_inst.run()
            self._run_tool(cmd, args=args, cwd=cwd)
