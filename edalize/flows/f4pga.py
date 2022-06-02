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
        ("vpr", [], {"arch": "xilinx", "arch_xml": "${F4PGA_ENV_SHARE}/arch/xc7a50t_test/arch.timing.xml", "vpr_options": []})
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

        # Variables
        
        # FASM and bitstream generation
        fasm_command = ["genfasm", "${ARCH_DEF}", "${EBLIF}", "--device ${DEVICE_NAME}", "${VPR_OPTIONS}", "--read_rr_graph ${RR_GRAPH}"]
        fasm_target = name + ".fasm"
        fasm_depend = name + ".route"

        bitstream_command = ["xcfasm", "--db-root ${DBROOT}", "--part ${PART}", "--part_file ${DBROOT}/${PART}/part.yaml", "--sparse --emit_pudc_b_pullup", "--fn_in ${FASM}", "--bit_out ${BIT}", "${FRM2BIT}"]
        bitstream_target = name + ".bit"
        bitstream_depend = name + ".fasm"

        self.commands.add(fasm_command, [fasm_target], [fasm_depend])
        self.commands.add(bitstream_command, [bitstream_target], [bitstream_depend])