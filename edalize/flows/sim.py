# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

from edalize.flows.generic import Generic


class Sim(Generic):
    """Run a simulation"""

    argtypes = ["plusarg", "vlogdefine", "vlogparam"]

    def run(self, args=None):
        tool = self.flow_options.get("tool")
        run_tool = self.flow.get_node(tool).inst

        # Get run command from simulator
        (cmd, args, cwd) = run_tool.run()
        self._run_tool(cmd, args=args, cwd=cwd)
