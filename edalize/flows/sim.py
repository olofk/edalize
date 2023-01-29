# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import os.path
from importlib import import_module

from edalize.flows.edaflow import Edaflow, FlowGraph


class Sim(Edaflow):
    """Run a simulation"""

    argtypes = ["plusarg", "vlogdefine", "vlogparam"]

    FLOW_DEFINED_TOOL_OPTIONS = {}

    FLOW_OPTIONS = {
        "frontends": {
            "type": "str",
            "desc": "Tools to run before linter (e.g. sv2v)",
            "list": True,
        },
        "tool": {
            "type": "str",
            "desc": "Select simulator",
        },
    }

    @classmethod
    def get_tool_options(cls, flow_options):
        flow = flow_options.get("frontends", []).copy()
        tool = flow_options.get("tool")
        if not tool:
            raise RuntimeError("Flow 'sim' requires flow option 'tool' to be set")
        flow.append(tool)

        return cls.get_filtered_tool_options(flow, cls.FLOW_DEFINED_TOOL_OPTIONS)

    def configure_flow(self, flow_options):
        # Check for mandatory flow option "tool"
        tool = self.flow_options.get("tool", "")
        if not tool:
            raise RuntimeError("Flow 'sim' requires flow option 'tool' to be set")

        # Start flow graph dict
        flow = {tool : {}}

        # Apply frontends
        deps = []
        for frontend in flow_options.get("frontends", []):
            flow[frontend] = {"deps" : deps}
            deps = [frontend]

        # Connect frontends to lint tool
        flow[tool]["deps"] = deps

        # Create and return flow graph object
        return FlowGraph.fromdict(flow)

    def configure_tools(self, graph):
        super().configure_tools(graph)

        # Set flow default target from simulator default target
        tool = self.flow_options.get("tool")
        self.commands.default_target = graph.get_node(tool).inst.default_target

        #self.run_tool = nodes[self.flow_options.get("tool")]

    def run(self, args):
        tool = self.flow_options.get("tool")
        run_tool = self.flow.get_node(tool).inst

        # Get run command from simulator
        (cmd, args, cwd) = run_tool.run(args)
        self._run_tool(cmd, args=args, cwd=cwd)
