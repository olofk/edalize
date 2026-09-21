# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

from edalize.flows.generic import Generic


class Libero(Generic):
    """
    The Libero flow executes Microsemi Libero SoC to create a bitstream and
    FPExpress to program a board.
    """

    argtypes = ["generic", "vlogdefine", "vlogparam"]

    FLOW_OPTIONS = {
        **Generic.FLOW_OPTIONS,
        **{
            "libero_options": {
                "type": "str",
                "desc": "libero options defined in edalize/tools/libero.py",
                "list": True,
            },
            "pgm": {
                "type": "bool",
                "desc": "Program board after bitstream is complete",
            },
        },
    }

    def configure_tools(self, graph):
        self.edam["tool_options"]["libero"] = self.flow_options.get("libero_options")
        super().configure_tools(graph)

    def run(self):
        if not self.flow_options.get("pgm"):
            return

        # Get run command from tool instance
        libero_inst = self.flow.get_node("libero").inst
        (cmd, args, cwd) = libero_inst.run()
        self._run_tool(cmd, args=args, cwd=cwd)
