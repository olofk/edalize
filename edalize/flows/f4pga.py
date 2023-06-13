# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import os.path

from edalize.flows.edaflow import Edaflow


class F4pga(Edaflow):
    """Edalize back-end implementation of F4PGA (Free and Open-Source Flow For FPGAs)"""

    """Currently supports Xilinx 7-series chips"""

    # F4PGA defined inputs to the underlying tools
    FLOW_DEFINED_TOOL_OPTIONS = {}

    # Inputs to the F4PGA flow
    FLOW_OPTIONS = {
        # Required (used by Yosys)
        "device": {"type": "str", "desc": "Example: 'artix7'"},
        # Required (used by Yosys)
        "part": {"type": "str", "desc": "Example: 'xc7a35tcpg236-1'"},
        # Required (used by VPR)
        "chip": {"type": "str", "desc": "Example: 'xc7a50t_test'"},
        # Optional, defaults to xilinx
        "arch": {
            "type": "str",
            "desc": "Targeting architecture for Yosys. Currently supported is 'xilinx' and that is the default if none specified.",
        },
        # Optional, defaults to VPR
        "pnr": {
            "type": "str",
            "desc": "Place and route tool. Valid options are 'vpr'/'vtr' and 'nextpnr'. Defaults to VPR.",
        },
        # Optional, if empty uses default F4PGA VPR options
        "vpr_options": {
            "type": "list",
            "desc": "Options to VPR, if the standard F4PGA values are not sufficient",
        },
    }

    # Standard F4PGA command line arguments to VPR
    DEFAULT_VPR_OPTIONS = [
        "--max_router_iterations",
        "500",
        "--routing_failure_predictor",
        "off",
        "--router_high_fanout_threshold",
        "-1",
        "--constant_net_method",
        "route",
        "--route_chan_width",
        "500",
        "--router_heap",
        "bucket",
        "--clock_modeling",
        "route",
        "--place_delta_delay_matrix_calculation_method",
        "dijkstra",
        "--place_delay_model",
        "delta",
        "--router_lookahead",
        "extended_map",
        "--check_route",
        "quick",
        "--strict_checks",
        "off",
        "--allow_dangling_combinational_nodes",
        "on",
        "--disable_errors",
        "check_unbuffered_edges:check_route",
        "--congested_routing_iteration_threshold",
        "0.8",
        "--incremental_reroute_delay_ripup",
        "off",
        "--base_cost_type",
        "delay_normalized_length_bounded",
        "--bb_factor",
        "10",
        "--acc_fac",
        "0.7",
        "--astar_fac",
        "1.8",
        "--initial_pres_fac",
        "2.828",
        "--pres_fac_mult",
        "1.2",
        "--check_rr_graph",
        "off",
        "--suppress_warnings",
        "sum_pin_class:check_unbuffered_edges:load_rr_indexed_data_T_values:check_rr_node:trans_per_R:check_route:set_rr_graph_tool_comment:calculate_average_switch",
    ]

    # Creates the flow tree with Yosys and VPR or NextPNR nodes
    def configure_flow(self, flow_options):

        # Set target
        # toplevel = self.edam["toplevel"]
        self.name = self.edam["name"]
        self.commands.set_default_target(f"{self.name}.bit")

        # Set up nodes
        synth_tool = "yosys"
        self.pnr_tool = flow_options.get("pnr", "vpr")
        if not self.pnr_tool in ["vpr", "nextpnr"]:
            raise RuntimeError(f"F4PGA flow error: invalid P&R tool: {self.pnr_tool}")

        self.device = flow_options.get("device")
        if not self.device:
            raise RuntimeError("F4PGA flow error: missing 'device' specifier")

        self.part = flow_options.get("part")
        if not self.part:
            raise RuntimeError("F4PGA flow error: missing 'part' specifier")

        self.db_dir = "$(shell prjxray-config)/"
        part_json = self.db_dir + f"{self.device}/{self.part}/part.json"

        chip = flow_options.get("chip")
        if not chip:
            raise RuntimeError("F4PGA flow error: missing 'chip' specifier")

        arch_dir = "${F4PGA_SHARE_DIR}/arch/"
        self.arch_xml = arch_dir + f"{chip}/arch.timing.xml"

        # Set up node options
        synth_options = {}

        # If arch is not configured, default to xilinx (will be changed in the future)
        if "arch" in flow_options:
            synth_options.update({"arch": flow_options.get("arch")})
        else:
            synth_options.update({"arch": "xilinx"})

        # If NextPNR, target JSON netlist, otherwise target EBLIF netlist for VPR
        if self.pnr_tool == "nextpnr":
            synth_options.update({"output_format": "json"})
        else:
            synth_options.update({"output_format": "eblif"})

        # If NextPNR, use built in Yosys template script, otherwise for VPR use custom F4PGA script
        if self.pnr_tool != "nextpnr":
            synth_options.update(
                {"yosys_template": "$(shell python3 -m f4pga.wrappers.tcl)"}
            )
            synth_options.update({"f4pga_synth_part_file": part_json})

        pnr_options = {}
        if self.pnr_tool == "vpr":
            self.eblif_file = f"{self.name}.eblif"
            pnr_options.update({"arch_xml": self.arch_xml})
            pnr_options.update(
                {
                    "generate_constraints": [
                        self.eblif_file,
                        f"{self.name}.net",
                        self.part,
                        chip,
                        self.arch_xml,
                    ]
                }
            )
            self.rr_graph_file = arch_dir + f"{chip}/rr_graph_{chip}.rr_graph.real.bin"
            lookahead_file = arch_dir + f"{chip}/rr_graph_{chip}.lookahead.bin"
            place_delay_file = arch_dir + f"{chip}/rr_graph_{chip}.place_delay.bin"
            self.device_name = chip.replace("_", "-")
            self.VPR_OPTIONS = flow_options.get("vpr_options", self.DEFAULT_VPR_OPTIONS)
            pnr_options.update(
                {
                    "vpr_options": [
                        "--device",
                        self.device_name,
                        "--read_rr_graph",
                        self.rr_graph_file,
                        "--read_router_lookahead",
                        lookahead_file,
                        "--read_placement_delay_lookup",
                        place_delay_file,
                    ]
                    + self.VPR_OPTIONS
                }
            )
        elif self.pnr_tool == "nextpnr":
            pnr_options.update({"arch": flow_options.get("arch", "xilinx")})

        return [
            (synth_tool, [self.pnr_tool], synth_options),
            (self.pnr_tool, [], pnr_options),
        ]

    # Adds the FASM and bitstream generation
    def configure_tools(self, nodes):
        super().configure_tools(nodes)

        if self.pnr_tool != "nextpnr":
            target = f"{self.name}.fasm"
            depends = f"{self.name}.analysis"
            command = (
                [
                    "genfasm",
                    self.arch_xml,
                    self.eblif_file,
                    "--device",
                    self.device_name,
                ]
                + self.VPR_OPTIONS
                + [
                    "--read_rr_graph",
                    self.rr_graph_file,
                    ";",
                    "cat",
                    f"{self.name}_fasm_extra.fasm",
                    ">>",
                    f"{self.name}.fasm",
                    ";",
                    "mv",
                    "vpr_stdout.log",
                    "fasm.log",
                ]
            )
            self.commands.add(command, [target], [depends])

        target = f"{self.name}.bit"
        depends = f"{self.name}.fasm"
        command = [
            "xcfasm",
            "--db-root",
            self.db_dir + self.device,
            "--part",
            self.part,
            "--part_file",
            self.db_dir + f"{self.device}/{self.part}/part.yaml",
            "--sparse",
            "--emit_pudc_b_pullup",
            "--fn_in",
            depends,
            "--bit_out",
            target,
        ]
        self.commands.add(command, [target], [depends])
