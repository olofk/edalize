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

    FLOW = []

    FLOW_OPTIONS = {
        "arch": {
            "type": "String",
            "desc": "The architecture name for Yosys (e.g. 'xilinx')"
        },
        "device_type": {
            "type": "String",
            "desc": "The device type (e.g. 'artix7')"
        },
        "device_name": {
            "type": "String",
            "desc": "The device name (e.g. 'xc7a50t_test')"
        },
        "part": {
            "type": "String",
            "desc": "The part name (e.g. 'xc7a35tcpg236-1')"
        },
        "pnr": {
            "type": "String",
            "desc": "The Place and Route tool (e.g. 'vpr' or 'nextpnr')"
        }
    }

    def get_output_format(self, pnr_tool):
        if pnr_tool == "vpr":
            return "eblif"
        if pnr_tool == "nextpnr":
            return "json"

    def get_synth_node(self, pnr_tool):
        if pnr_tool == "vpr":
            return ("yosys", [pnr_tool], {
                "output_format": "eblif",
                "yosys_template": "${F4PGA_ENV_SHARE}/scripts/xc7/synth.tcl",
                "split_io": [
                    "${F4PGA_ENV_SHARE}/scripts/split_inouts.py",   # Python script
                    "${OUT_JSON}", # infile name
                    "${SYNTH_JSON}", # outfile name
                    "${F4PGA_ENV_SHARE}/scripts/xc7/conv.tcl" # End TCL script
            ]})
        if pnr_tool == "nextpnr":
            return ("yosys", [pnr_tool], {
                "output_format": "json",
            })

        

    def get_pnr_node(self, pnr_tool):
        if pnr_tool == "vpr":
            return ("vpr", [], {
                "arch_xml": "${F4PGA_ENV_SHARE}/arch/${DEVICE_NAME}/arch.timing.xml", 
                "input_type": "eblif",
                "vpr_options": [
                    "${VPR_OPTIONS}",
                    "--read_rr_graph ${RR_GRAPH}",
                    "--read_router_lookahead ${LOOKAHEAD}",
                    "--read_placement_delay_lookup ${PLACE_DELAY}" 
                ],
                "gen_constraints": [
                    [
                        "${PYTHON}",
                        "${IOGEN}",
                        "--blif ${OUT_EBLIF}",
                        "--map ${PINMAP_FILE}",
                        "--net ${NET_FILE}",
                        "> ${IOPLACE_FILE}"
                    ],
                    [
                        "${PYTHON}",
                        "${CONSTR_GEN}",
                        "--net ${NET_FILE}",
                        "--arch ${ARCH_DEF}",
                        "--blif ${OUT_EBLIF}",
                        "--vpr_grid_map ${VPR_GRID_MAP}",
                        "--input ${IOPLACE_FILE}",
                        "--db_root ${DATABASE_DIR} " 
                        "--part ${PART}",
                        "> ${CONSTR_FILE}"
                    ],
                    "${IOPLACE_FILE}",
                    "${CONSTR_FILE}"
                ]})
        if pnr_tool == "nextpnr":
            return ("nextpnr", [], {
                "nextpnr_options": []
                })

    def __init__(self, edam, work_root, verbose=False):
        # Read Place and Route tool if specified, otherwise default to VPR
        self.pnr_tool = edam.get("flow_options", {}).get("pnr", "vpr")

        # Build flow using class methods
        self.FLOW.append(self.get_synth_node(self.pnr_tool))
        self.FLOW.append(self.get_pnr_node(self.pnr_tool))

        Edaflow.__init__(self, edam, work_root, verbose)
        self.name = self.edam["name"]
        self.bitstream_file = f"{self.name}.bit"
        self.openocd_config_file = "openocd.txt"

    def build_tool_graph(self):
        return super().build_tool_graph()

    def configure_openocd(self):
        device_name = self.flow_options["device_name"]
        file_path = os.path.join(self.work_root, self.openocd_config_file)

        with open(file_path, "w") as file:
            if device_name.startswith("xc7"):
                lines = [
                    "interface ftdi\n", 
                    "ftdi_device_desc \"Digilent USB Device\"\n",
                    "ftdi_vid_pid 0x0403 0x6010\n",
                    "ftdi_channel 0\n",
                    "ftdi_layout_init 0x0088 0x008b\n",
                    "reset_config none\n",
                    "adapter_khz 10000\n",
                    "source [find cpld/xilinx-xc7.cfg]\n",
                    "source [find cpld/jtagspi.cfg]\n",
                    "init\n",
                    "puts [irscan xc7.tap 0x09]\n",
                    "puts [drscan xc7.tap 32 0]\n",
                    "puts \"Programming FPGA...\"\n",
                    f"pld load 0 {self.bitstream_file}\n",
                    "exit\n"]
                file.writelines(lines)

    def configure_tools(self, nodes):
        # Configure nodes    
        super().configure_tools(nodes)

        name = self.edam["name"]
        top = self.edam["toplevel"]
        self.commands.set_default_target("${BITSTREAM_FILE}")

        constraint_file_list = []
        for f in self.edam["files"]:
            if f["file_type"] in ["xdc"]:
                constraint_file_list.append(f["name"])

        # F4PGA Variables
        self.commands.add_env_var("NET_FILE", f"{self.name}.net")
        self.commands.add_env_var("ANALYSIS_FILE", f"{self.name}.analysis")
        
        if self.pnr_tool == "vpr":
            # VPR genfasm command generates a fasm file that matches the top module name, by default
            self.commands.add_env_var("FASM_FILE", f"{top}.fasm")
        else:
            # NextPNR generates fasm file that matches the project name by default
            self.commands.add_env_var("FASM_FILE", f"{self.name}.fasm")

        self.commands.add_env_var("BITSTREAM_FILE", self.bitstream_file)

        self.commands.add_env_var("DEVICE_TYPE", self.flow_options["device_type"])
        self.commands.add_env_var("DEVICE_NAME", self.flow_options["device_name"])
        self.commands.add_env_var("DEVICE_NAME_MODIFIED", "$(shell echo ${DEVICE_NAME} | sed -n 's/_/-/p')")
        self.commands.add_env_var("PART", self.flow_options["part"])
        self.commands.add_env_var("TOP", f"{top}")

        self.commands.add_env_var("INPUT_XDC_FILES", ' '.join(constraint_file_list))
        self.commands.add_env_var("PYTHON", "python3")

        self.commands.add_env_var("USE_ROI", "\"FALSE\"")
        self.commands.add_env_var("TECHMAP_PATH", "${F4PGA_ENV_SHARE}/techmaps/xc7_vpr/techmap")
        self.commands.add_env_var("DATABASE_DIR", "$(shell prjxray-config)")
        self.commands.add_env_var("PART_JSON", "${DATABASE_DIR}/${DEVICE_TYPE}/${PART}/part.json")
        self.commands.add_env_var("OUT_FASM_EXTRA", f"{self.name}_fasm_extra.fasm")
        self.commands.add_env_var("OUT_SDC", f"{self.name}.sdc")
        self.commands.add_env_var("OUT_SYNTH_V", f"{self.name}_synth.v")
        self.commands.add_env_var("OUT_JSON", f"{self.name}.json")
        self.commands.add_env_var("PYTHON3", "$(shell which python3)")
        self.commands.add_env_var("UTILS_PATH", "${F4PGA_ENV_SHARE}/scripts")
        self.commands.add_env_var("SYNTH_JSON", f"{self.name}_io.json")
        self.commands.add_env_var("OUT_EBLIF", f"{self.name}.eblif")
        self.commands.add_env_var("ARCH_DIR", "${F4PGA_ENV_SHARE}/arch/${DEVICE_NAME}")
        self.commands.add_env_var("RR_GRAPH", "${ARCH_DIR}/rr_graph_${DEVICE_NAME}.rr_graph.real.bin")
        self.commands.add_env_var("LOOKAHEAD", "${ARCH_DIR}/rr_graph_${DEVICE_NAME}.lookahead.bin")
        self.commands.add_env_var("PLACE_DELAY", "${ARCH_DIR}/rr_graph_${DEVICE_NAME}.place_delay.bin")
        self.commands.add_env_var("ARCH_DEF", "${ARCH_DIR}/arch.timing.xml")
        self.commands.add_env_var("DBROOT", "${DATABASE_DIR}/${DEVICE_TYPE}")
        self.commands.add_env_var("IOGEN", "${F4PGA_ENV_SHARE}/scripts/prjxray_create_ioplace.py")
        self.commands.add_env_var("CONSTR_GEN", "${F4PGA_ENV_SHARE}/scripts/prjxray_create_place_constraints.py")
        self.commands.add_env_var("CONSTR_FILE", "constraints.place")
        self.commands.add_env_var("PINMAP_FILE", "${ARCH_DIR}/${PART}/pinmap.csv")
        self.commands.add_env_var("VPR_GRID_MAP", "${ARCH_DIR}/vpr_grid_map.csv")
        self.commands.add_env_var("IOPLACE_FILE", f"{self.name}.ioplace")

        self.commands.add_env_var("OUT_NOISY_WARNINGS", "noisy_warnings-${DEVICE_NAME}_fasm.log")
        self.commands.add_env_var("VPR_OPTIONS", ' '.join([
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
                "--suppress_warnings ${OUT_NOISY_WARNINGS},sum_pin_class:check_unbuffered_edges:load_rr_indexed_data_T_values:check_rr_node:trans_per_R:check_route:set_rr_graph_tool_comment:calculate_average_switch",
        ]))
        
        # FASM and bitstream generation
        if self.pnr_tool == "vpr":
            fasm_command = ["genfasm", "${ARCH_DEF}", "${OUT_EBLIF}", "--device ${DEVICE_NAME_MODIFIED}", "${VPR_OPTIONS}", "--read_rr_graph ${RR_GRAPH}"]
            fasm_target = "${FASM_FILE}"
            fasm_depend = "${ANALYSIS_FILE}"
            self.commands.add(fasm_command, [fasm_target], [fasm_depend])

        bitstream_command = ["xcfasm", "--db-root ${DBROOT}", "--part ${PART}", "--part_file ${DBROOT}/${PART}/part.yaml", "--sparse --emit_pudc_b_pullup", "--fn_in ${FASM_FILE}", "--bit_out ${BITSTREAM_FILE}", "${FRM2BIT}"]
        bitstream_target = "${BITSTREAM_FILE}"
        bitstream_depend = "${FASM_FILE}"
        self.commands.add(bitstream_command, [bitstream_target], [bitstream_depend])

        # Create openocd configuration file for download/run
        self.configure_openocd()

    def set_run_command(self):
        self.commands.add(["openocd", "-f", self.openocd_config_file], ["run"], ["pre_run"])
