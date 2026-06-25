# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

from __future__ import annotations

import os.path
from importlib import import_module
from typing import Any

from edalize.flows.edaflow import Edaflow, FlowGraph, FlowNodeSpec


class Generic(Edaflow):
    """Run an arbitrary tool"""

    argtypes = ["cmdlinearg", "generic", "plusarg", "vlogdefine", "vlogparam"]

    FLOW_DEFINED_TOOL_OPTIONS: dict[str, dict[str, Any]] = {}

    FLOW_OPTIONS = {
        **Edaflow.FLOW_OPTIONS,
        **{
            "tool": {
                "type": "str",
                "desc": "Select tool",
            },
        },
    }

    @classmethod
    def get_tool_options(cls, flow_options: dict[str, Any]) -> dict[str, Any]:
        flow = flow_options.get("frontends", []).copy()
        tool = cls._require_flow_option(flow_options, "tool")
        flow.append(tool)

        return cls.get_filtered_tool_options(flow, cls.FLOW_DEFINED_TOOL_OPTIONS)

    def configure_flow(self, flow_options: dict[str, Any]) -> FlowGraph:
        # Check for mandatory flow option "tool"
        tool = self._require_flow_option(flow_options, "tool")

        # Apply flow-defined tool options if any
        fdto = self.FLOW_DEFINED_TOOL_OPTIONS.get(tool, {})

        # Start flow graph dict
        flow: dict[str, FlowNodeSpec] = {tool: {"fdto": fdto}}

        # Apply frontends
        deps: list[str] = []
        for frontend in flow_options.get("frontends", []):
            flow[frontend] = {"deps": deps}
            deps = [frontend]

        # Connect frontends to main tool
        flow[tool]["deps"] = deps

        # Create and return flow graph object
        return FlowGraph.fromdict(flow)

    def configure_tools(self, graph: FlowGraph) -> None:
        super().configure_tools(graph)

        # Set flow default target from the main tool's default target
        tool = self.flow_options.get("tool")

        self.commands.default_target = graph.get_node(tool).inst.commands.default_target
