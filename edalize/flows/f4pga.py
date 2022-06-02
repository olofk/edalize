# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import os.path

from edalize.flows.edaflow import Edaflow

class F4pga(Edaflow):
    """
    Free and open-source 'flow for FPGA's'. 
    
    Uses Yosys for synthesys and VPR or NextPNR for place and route.
    """

    FLOW = [
        ("yosys", ["vpr"], {"arch": "xilinx", "output_format": "blif"}),
        ("vpr", [], {"arch": "xilinx", "arch_xml": "${shareDir}/arch/xc7a50t_test/arch.timing.xml", "vpr_options": []})
    ]

    FLOW_OPTIONS = {}

    def __init__(self, edam, work_root, verbose=False):
        Edaflow.__init__(self, edam, work_root, verbose)

    def build_tool_graph(self):
        return super().build_tool_graph()

    def configure_tools(self, nodes):
        super().configure_tools(nodes)
        name = self.edam["name"]
        self.commands.set_default_target(name + ".bit")