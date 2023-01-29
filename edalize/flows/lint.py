# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import os.path
from importlib import import_module

from edalize.flows.edaflow import Edaflow, FlowGraph


class Lint(Edaflow):
    """Run a linter tool on the design"""

    argtypes = ["vlogdefine", "vlogparam"]

    FLOW_DEFINED_TOOL_OPTIONS = {
        "verilator": {"mode": "lint-only", "exe": "false", "make_options": []},
        # verible, spyglass, ascentlint, slang...
    }

    FLOW_OPTIONS = {
        "frontends": {
            "type": "str",
            "desc": "Tools to run before linter (e.g. sv2v)",
            "list": True,
        },
        "tool": {
            "type": "str",
            "desc": "Select Lint tool",
        },
    }

    @classmethod
    def get_tool_options(cls, flow_options):
        flow = flow_options.get("frontends", []).copy()
        tool = flow_options.get("tool")
        if not tool:
            raise RuntimeError("Flow 'lint' requires flow option 'tool' to be set")
        flow.append(tool)

        return cls.get_filtered_tool_options(flow, cls.FLOW_DEFINED_TOOL_OPTIONS)

    def configure_flow(self, flow_options):
        # Check for mandatory flow option "tool"
        tool = self.flow_options.get("tool", "")
        if not tool:
            raise RuntimeError("Flow 'lint' requires flow option 'tool' to be set")

        # Apply flow-defined tool options if any
        fdto = self.FLOW_DEFINED_TOOL_OPTIONS.get(tool, {})

        # Start flow graph dict
        flow = {tool : {"fdto" : fdto}}

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

        # Set flow default target from the lint tool's default target
        tool = self.flow_options.get("tool")

        self.commands.default_target = graph.get_node(tool).inst.default_target
