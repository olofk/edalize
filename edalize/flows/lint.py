# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import os.path
from importlib import import_module

from edalize.flows.edaflow import Edaflow, FlowGraph

class Lint(Generic):
    """Run a lint tool on the design"""

    argtypes = ["cmdlinearg", "generic", "plusarg", "vlogdefine", "vlogparam"]

    FLOW_DEFINED_TOOL_OPTIONS = {
        "verilator": {
            "mode": "lint-only", "exe": "false", "make_options": []
            },
        "spyglass": {
            "methodology": "GuideWare/latest/block/rtl_handoff",
            "goals": ["lint/lint_rtl"],
            "goal_options": [],
            "options": [],
            "rule_parameters": [],
        },
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
    # verible, ascentlint, slang...

    @classmethod
    def get_tool_options(cls, flow_options):
        flow = flow_options.get("frontends", []).copy()
        tool = flow_options.get("tool")
        if not tool:
            raise RuntimeError("Flow 'lint' requires flow option 'tool' to be set")
        flow.append(tool)
        return cls.get_filtered_tool_options(flow, cls.FLOW_DEFINED_TOOL_OPTIONS)

  def configure_flow(self, flow_options):
        tool = self.flow_options.get("tool", "")
        if not tool:
            raise RuntimeError("Flow 'lint' requires flow option 'tool' to be set")
        fdto = self.FLOW_DEFINED_TOOL_OPTIONS.get(tool, {})
        flow = {tool : {"fdto" : fdto}}
        deps = []
        for frontend in flow_options.get("frontends", []):
            flow[frontend] = {"deps" : deps}
            deps = [frontend]
        flow[tool]["deps"] = deps
        return FlowGraph.fromdict(flow)

    def configure_tools(self, graph):
        super().configure_tools(graph)
        tool = self.flow_options.get("tool")
        self.commands.default_target = graph.get_node(tool).inst.commands.default_target
