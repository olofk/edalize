# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import os.path

from edalize.flows.edaflow import Edaflow


class Vivado(Edaflow):
    """The Vivado backend executes Xilinx Vivado to build systems and program the FPGA"""

    argtypes = ["vlogdefine", "vlogparam"]

    FLOW = [
        ("yosys", ["vivado"], {"arch": "xilinx", "output_format": "edif"}),
        ("vivado", [], {}),
    ]

    FLOW_OPTIONS = {
        "pnr": {
            "type": "String",
            "desc": "Select Place & Route tool.",
        },
        "synth": {
            "type": "String",
            "desc": "Synthesis tool. Allowed values are vivado (default) and yosys.",
        },
    }

    def __init__(self, edam, work_root, verbose=False):
        if edam.get("flow_options", {}).get("synth", {}) != "yosys":
            # Remove from flow Yosys node
            self.FLOW = [("vivado", [], {})]
        Edaflow.__init__(self, edam, work_root, verbose)

    def build_tool_graph(self):
        return super().build_tool_graph()

    def configure_tools(self, nodes):
        super().configure_tools(nodes)
        name = self.edam["name"]
        self.commands.set_default_target(name + ".bit")
