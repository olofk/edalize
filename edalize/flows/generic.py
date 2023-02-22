# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import os.path
from importlib import import_module

from edalize.flows.edaflow import Edaflow, FlowGraph


class Generic(Edaflow):
    """Run an arbitrary tool"""

    argtypes = ["cmdlinearg", "generic", "plusarg", "vlogdefine", "vlogparam"]

    FLOW_DEFINED_TOOL_OPTIONS = {}

    FLOW_OPTIONS = {
        "frontends": {
            "type": "str",
            "desc": "Tools to run before main flow",
            "list": True,
        },
        "tool": {
            "type": "str",
            "desc": "Select tool",
        },
    }

    @classmethod
    def get_tool_options(cls, flow_options):
        flow = flow_options.get("frontends", []).copy()
        tool = cls._require_flow_option(flow_options, "tool")
        flow.append(tool)

        return cls.get_filtered_tool_options(flow, cls.FLOW_DEFINED_TOOL_OPTIONS)

    def configure_flow(self, flow_options):
        # Check for mandatory flow option "tool"
        tool = self.flow_options.get("tool", "")

        # Apply flow-defined tool options if any
        fdto = self.FLOW_DEFINED_TOOL_OPTIONS.get(tool, {})

        # Start flow graph dict
        flow = {tool: {"fdto": fdto}}

        # Apply frontends
        deps = []
        for frontend in flow_options.get("frontends", []):
            flow[frontend] = {"deps": deps}
            deps = [frontend]

        # Connect frontends to main tool
        flow[tool]["deps"] = deps

        # Create and return flow graph object
        return FlowGraph.fromdict(flow)

    def configure_tools(self, graph):
        super().configure_tools(graph)

        # Set flow default target from the main tool's default target
        tool = self.flow_options.get("tool")

        self.commands.default_target = graph.get_node(tool).inst.commands.default_target
