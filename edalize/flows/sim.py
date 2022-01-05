# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import os.path

from edalize.flows.edaflow import Edaflow


class Sim(Edaflow):
    """Run a simulation"""

    argtypes = ["plusarg", "vlogdefine", "vlogparam"]

    FLOW = [
        ("verilator", [], {}),
        # verible, spyglass, ascentlint, slang...
    ]

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

    def build_tool_graph(self):
        tool = self.flow_options.get("tool", "")

        if not tool:
            raise RuntimeError("Flow 'sim' requires flow option 'tool' to be set")
        known_tools = [x[0] for x in self.FLOW]

        self.FLOW = [x for x in self.FLOW if x[0] == tool]

        if not self.FLOW:
            raise RuntimeError(
                f"Unknown tool {tool!r}. Allowed options are {', '.join(known_tools)}"
            )

        # FIXME: This makes an assumption that the first tool in self.FLOW is
        # a single entry point to the flow
        next_tool = self.FLOW[0][0]

        for frontend in reversed(self.flow_options.get("frontends", [])):
            self.FLOW[0:0] = [(frontend, [next_tool], {})]
            next_tool = frontend
        return super().build_tool_graph()

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
