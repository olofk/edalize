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
        ("yosys", ["vpr"], {
            "arch": "xilinx", 
            "output_format": "eblif",
            "yosys_template": "${F4PGA_ENV_SHARE}/scripts/xc7/synth.tcl",
            "yosys_synth_options": [],
            "split_io": [
                "${F4PGA_ENV_SHARE}/scripts/split_inouts.py",   # Python script
                "${OUT_JSON}", # infile name
                "${SYNTH_JSON}", # outfile name
                "${F4PGA_ENV_SHARE}/scripts/xc7/conv.tcl" # End TCL script
                ]}),
        ("vpr", [], {
            "arch_xml": "${F4PGA_ENV_SHARE}/arch/xc7a50t_test/arch.timing.xml", 
            "input_type": "eblif",
            "vpr_options": [
                "--disp on",
                "--max_router_iterations 500",
                "--routing_failure_predictor off",
                "--router_high_fanout_threshold -1",
                "--constant_net_method route",
                "--route_chan_width 500",
                "--router_heap bucket",
                "--clock_modeling route",
                "--place_delta_delay_matrix_calculation_method dijkstra",
                "--place_delay_model delta",
                "--router_lookahead extended_map",
                "--check_route quick",
                "--strict_checks off",
                "--allow_dangling_combinational_nodes on",
                "--disable_errors check_unbuffered_edges:check_route",
                "--congested_routing_iteration_threshold 0.8",
                "--incremental_reroute_delay_ripup off",
                "--base_cost_type delay_normalized_length_bounded",
                "--bb_factor 10",
                "--acc_fac 0.7",
                "--astar_fac 1.8",
                "--initial_pres_fac 2.828",
                "--pres_fac_mult 1.2",
                "--check_rr_graph off",
                "--suppress_warnings ${OUT_NOISY_WARNINGS},sum_pin_class:check_unbuffered_edges:load_rr_indexed_data_T_values:check_rr_node:trans_per_R:check_route:set_rr_graph_tool_comment:calculate_average_switch"
            ]})
    ]

    FLOW_OPTIONS = {}

    def __init__(self, edam, work_root, verbose=False):
        Edaflow.__init__(self, edam, work_root, verbose)

    def build_tool_graph(self):
        return super().build_tool_graph()

    def configure_tools(self, nodes):
        super().configure_tools(nodes)
        name = self.edam["name"]
        top = self.edam["toplevel"]
        self.commands.set_default_target("${BITSTREAM_FILE}")

        verilog_file_list = []
        constraint_file_list = []
        for f in self.edam["files"]:
            if f["file_type"] in ["verilogSource"]:
                verilog_file_list.append(f["name"])
            if f["file_type"] in ["xdc"]:
                constraint_file_list.append(f["name"])

        # Variables
        self.commands.add_env_var("BITSTREAM_FILE", f"{top}.bit")

        self.commands.add_env_var("DEVICE", "artix7")
        self.commands.add_env_var("PART", "xc7a35tcpg236-1")
        self.commands.add_env_var("TOP", f"{top}")

        self.commands.add_env_var("INPUT_XDC_FILES", ' '.join(constraint_file_list))

        self.commands.add_env_var("USE_ROI", "\"FALSE\"")
        self.commands.add_env_var("TECHMAP_PATH", "${F4PGA_ENV_SHARE}/techmaps/xc7_vpr/techmap")
        self.commands.add_env_var("DATABASE_DIR", "$(shell prjxray-config)")
        self.commands.add_env_var("PART_JSON", "${DATABASE_DIR}/${DEVICE}/${PART}/part.json")
        self.commands.add_env_var("OUT_FASM_EXTRA", f"{top}_fasm_extra.fasm")
        self.commands.add_env_var("OUT_SDC", f"{top}.sdc")
        self.commands.add_env_var("OUT_SYNTH_V", f"{top}_synth.v")
        self.commands.add_env_var("OUT_JSON", f"{top}.json")
        self.commands.add_env_var("PYTHON3", f"$(shell which python3)")
        self.commands.add_env_var("UTILS_PATH", "${F4PGA_ENV_SHARE}/scripts")
        self.commands.add_env_var("SYNTH_JSON", f"{top}_io.json")
        self.commands.add_env_var("OUT_EBLIF", f"{top}.eblif")
        
        # FASM and bitstream generation
        fasm_command = ["genfasm", "${ARCH_DEF}", "${EBLIF}", "--device ${DEVICE_NAME}", "${VPR_OPTIONS}", "--read_rr_graph ${RR_GRAPH}"]
        fasm_target = f"{name}.fasm"
        fasm_depend = f"{name}.analysis"

        bitstream_command = ["xcfasm", "--db-root ${DBROOT}", "--part ${PART}", "--part_file ${DBROOT}/${PART}/part.yaml", "--sparse --emit_pudc_b_pullup", "--fn_in ${FASM}", "--bit_out ${BITSTREAM_FILE}", "${FRM2BIT}"]
        bitstream_target = "${BITSTREAM_FILE}"
        bitstream_depend = f"{name}.fasm"

        self.commands.add(fasm_command, [fasm_target], [fasm_depend])
        self.commands.add(bitstream_command, [bitstream_target], [bitstream_depend])