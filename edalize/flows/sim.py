# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import os.path
from importlib import import_module

from edalize.flows.edaflow import Edaflow


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
        flow = flow_options.get("frontends", [])
        tool = flow_options.get("tool")
        if not tool:
            raise RuntimeError("Flow 'sim' requires flow option 'tool' to be set")
        flow.append(tool)

        return cls.get_filtered_tool_options(flow, cls.FLOW_DEFINED_TOOL_OPTIONS)

    def configure_flow(self, flow_options):
        tool = self.flow_options.get("tool", "")
        if not tool:
            raise RuntimeError("Flow 'sim' requires flow option 'tool' to be set")
        flow = [(tool, [], {})]
        # Add any user-specified frontends to the flow
        next_tool = tool

        for frontend in reversed(flow_options.get("frontends", [])):
            flow[0:0] = [(frontend, [next_tool], {})]
            next_tool = frontend
        return flow

    def configure_tools(self, nodes):
        super().configure_tools(nodes)

        self.commands.default_target = nodes[
            self.flow_options.get("tool")
        ].default_target
        # fixme
        self.run_tool = nodes[self.flow_options.get("tool")]

    def run(self, args):
        (cmd, args, cwd) = self.run_tool.run(args)
        self._run_tool(cmd, args=args, cwd=cwd)
