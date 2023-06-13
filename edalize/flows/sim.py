# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

from edalize.flows.generic import Generic


class Sim(Generic):
    """Run a simulation"""

    argtypes = ["plusarg", "vlogdefine", "vlogparam"]

    FLOW_OPTIONS = {
        **Generic.FLOW_OPTIONS,
        **{
            "cocotb_module": {
                "type": "str",
                "desc": "Cocotb test python module. (Enables Cocotb simulations)",
            },
        },
    }

    def configure_tools(self, flow):
        if self.flow_options.get("cocotb_module"):
            tool = self.flow_options.get("tool")
            cocotb_options = {
                "icarus": (
                    "vvp_options",
                    [
                        "-M",
                        "`cocotb-config --lib-dir`",
                        "-m",
                        "`cocotb-config --lib-name vpi icarus`",
                    ],
                ),
                "modelsim": (
                    "vsim_options",
                    ["-pli", "`cocotb-config --lib-name-path vpi questa`"],
                ),
            }
            (opt, val) = cocotb_options[tool]
            self.edam["tool_options"][tool][opt] = (
                self.edam["tool_options"][tool].get(opt, []) + val
            )

        super().configure_tools(flow)

    def run(self, args=None):
        tool = self.flow_options.get("tool")
        run_tool = self.flow.get_node(tool).inst

        # Get run command from simulator
        (cmd, args, cwd) = run_tool.run()
        cocotb_module = self.flow_options.get("cocotb_module")
        env = {"MODULE": cocotb_module} if cocotb_module else {}
        self._run_tool(cmd, args=args, cwd=cwd, env=env)
