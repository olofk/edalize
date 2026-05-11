# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

from __future__ import annotations

from typing import Any

from edalize.flows.edaflow import Edaflow, FlowGraph


class Gls(Edaflow):
    """Run a gate-level simulation"""

    argtypes = ["plusarg", "vlogdefine", "vlogparam"]

    FLOW_OPTIONS = {
        **Edaflow.FLOW_OPTIONS,
        **{
            "synth": {
                "type": "str",
                "desc": "Synthesis tool",
            },
            "synth_top": {
                "type": "str",
                "desc": "Top module of synthesised part of the design",
            },
            "sim": {
                "type": "str",
                "desc": "Simulator",
            },
        },
    }

    FLOW_DEFINED_TOOL_OPTIONS: dict[str, dict[str, Any]] = {
        "yosys": {"output_format": "verilog"},
    }

    @classmethod
    def get_tool_options(cls, flow_options: dict[str, Any]) -> dict[str, Any]:
        flow = flow_options.get("frontends", []).copy()

        flow.append(cls._require_flow_option(flow_options, "synth"))

        flow.append(cls._require_flow_option(flow_options, "sim"))

        return cls.get_filtered_tool_options(flow, cls.FLOW_DEFINED_TOOL_OPTIONS)

    def configure_flow(self, flow_options: dict[str, Any]) -> FlowGraph:
        synth = flow_options.get("synth")

        # Apply flow-defined tool options if any
        fdto = self.FLOW_DEFINED_TOOL_OPTIONS.get(synth, {})

        # Start flow graph dict
        flow: dict[str, dict[str, Any]] = {synth: {"fdto": fdto}}

        # Apply frontends
        deps: list[str] = []
        for frontend in flow_options.get("frontends", []):
            flow[frontend] = {"deps": deps}
            deps = [frontend]

        # Connect frontends to synthesis tool
        flow[synth]["deps"] = deps

        sim = self.flow_options.get("sim")

        # Add simulator to flow graph dict
        flow[sim] = {
            "deps": [synth],
            "fdto": self.FLOW_DEFINED_TOOL_OPTIONS.get(sim, {}),
        }

        # Create and return flow graph object
        return FlowGraph.fromdict(flow)

    def configure_tools(self, graph: FlowGraph) -> None:
        input_edam = self.edam.copy()

        for frontend in self.flow_options.get("frontends", []):
            node = graph.get_node(frontend)
            node.inst.work_root = self.work_root
            node.inst.setup(input_edam)
            self.commands.commands += node.inst.commands.commands
            input_edam = node.inst.edam

        # Change toplevel for EDAM sent to synthesis tool
        input_edam["toplevel"] = self.flow_options.get("synth_top")

        node = graph.get_node(self.flow_options.get("synth"))
        node.inst.work_root = self.work_root
        node.inst.setup(input_edam)
        self.commands.commands += node.inst.commands.commands
        input_edam = node.inst.edam

        sim = self.flow_options.get("sim")
        input_edam["toplevel"] = self.edam["toplevel"]

        node = graph.get_node(sim)
        node.inst.work_root = self.work_root
        node.inst.setup(input_edam)
        self.commands.commands += node.inst.commands.commands

        # Hook up pre_build scripts (self.commands.commands[0]) to main flow
        self.commands.commands[1].order_only_deps = ["pre_build"]

        self.commands.default_target = graph.get_node(sim).inst.commands.default_target

    def run(self, args: Any = None) -> None:
        tool = self.flow_options.get("sim")
        run_tool = self.flow.get_node(tool).inst

        # Get run command from simulator
        (cmd, args, cwd) = run_tool.run()
        self._run_tool(cmd, args=args, cwd=cwd)
