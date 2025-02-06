# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import os

from edalize.flows.generic import Generic

class Sim(Generic):
    """Run a simulation"""

    argtypes = ["plusarg", "vlogdefine", "vlogparam"]

    FLOW_OPTIONS = {
        **Generic.FLOW_OPTIONS,
        **{
        },
    }

    def configure_tools(self, flow):
        super().configure_tools(flow)

    def configure(self):
        if self.flow_options.get("tool") == "vcs":
            with open(os.path.join(self.work_root, "pli.tab"), "w") as f:
                f.write("acc+=rw,wn:*\n")
        super().configure()

    def run(self, args=None):
        tool = self.flow_options.get("tool")
        run_tool = self.flow.get_node(tool).inst

        # Get run command from simulator
        (cmd, args, cwd) = run_tool.run()
        env = {} # used for cocotb
        
        self._run_tool(cmd, args=args, cwd=cwd, env=env)
