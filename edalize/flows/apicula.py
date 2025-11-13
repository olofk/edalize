# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import re

from edalize.flows.edaflow import Edaflow, FlowGraph


class Apicula(Edaflow):
    """Open source toolchain for Gowin FPGAs. Uses yosys for synthesis and nextpnr for Place & Route"""

    argtypes = ["vlogdefine", "vlogparam"]
    verbose = False

    _flow = {
        "yosys": {"fdto": {"arch": "gowin", "output_format": "json"}},
        "nextpnr": {"deps": ["yosys"], "fdto": {"arch": "gowin"}},
        "gowinpack": {"deps": ["nextpnr"], "fdto": {}},
        "openfpgaloader": {"deps": ["gowinpack"], "fdto": {}},
    }

    FLOW_OPTIONS = {
        **Edaflow.FLOW_OPTIONS,
        **{
            "board": {
                "type": "str",
                "desc": "Target board with FPGA",
            },
            "device": {
                "type": "str",
                "desc": "FPGA device code (e.g. GW1N-LV1QN48C6/I5)",
            },
            "device_family": {
                "type": "str",
                "desc": "FPGA device family code *C* or *none*",
            },
        },
    }

    BOARDS = {
        "tangnano": {
            "device": "GW1N-LV1QN48C6/I5",
        },
        "tangnano9k": {
            "device": "GW1NR-LV9QN88PC6/I5",
            "device_family": "C",
        },
        "tangnano20k": {
            "device": "GW2AR-LV18QN88C8/I7",
            "device_family": "C",
        },
    }

    @classmethod
    def get_tool_options(cls, flow_options):
        tools = flow_options.get("frontends", []) + list(cls._flow)

        flow_defined_tool_options = {}
        for tool, parameters in cls._flow.items():
            flow_defined_tool_options[tool] = parameters.get("fdto", {})
        return cls.get_filtered_tool_options(tools, flow_defined_tool_options)

    def configure_flow(self, flow_options):

        flow = self._flow.copy()

        # Add any user-specified frontends to the flow
        deps = []
        for frontend in flow_options.get("frontends", []):
            flow[frontend] = {"deps": deps}
            deps = [frontend]

        flow["yosys"]["deps"] = deps

        fs_file = self.edam["name"] + ".fs"
        self.commands.set_default_target(fs_file)

        board = flow_options.get("board", "")
        device = flow_options.get("device", "")
        device_family_code = flow_options.get("device_family", "")
        if board in self.BOARDS:
            if not device:
                device = self.BOARDS[board]["device"]
                if "device_family" in self.BOARDS[board]:
                    device_family_code = self.BOARDS[board]["device_family"]
        if not device:
            raise RuntimeError("Missing required option 'device' for apicula")
        if device_family_code not in ["", "C"]:
            raise RuntimeError(
                "Unknown device family code {}".format(device_family_code)
            )
        match = re.match("^GW(1N|2A|5A)[A-Z]*-[A-Z]V([0-9]+)", device)
        device_family = ""
        if match:
            device_family = "GW{}-{}{}".format(match[1], match[2], device_family_code)
        else:
            raise RuntimeError("Unknown device {}".format(device))

        self.device = device
        self.device_family = device_family
        self.board = board

        return FlowGraph.fromdict(flow)

    def configure_tools(self, flow):
        self.edam["tool_options"]["nextpnr"]["device"] = self.device
        self.edam["tool_options"]["gowinpack"]["device"] = self.device
        self.edam["tool_options"]["nextpnr"]["device_family"] = self.device_family
        self.edam["tool_options"]["gowinpack"]["device_family"] = self.device_family
        self.edam["tool_options"]["openfpgaloader"]["board"] = self.board

        super().configure_tools(flow)

    def build(self):
        (cmd, args) = self.build_runner.get_build_command()
        self._run_tool(cmd, args=args, cwd=self.work_root, quiet=True)

    def run(self):
        (cmd, args) = self.build_runner.get_build_command()
        args += ["openfpgaloader"]
        self._run_tool(cmd, args=args, cwd=self.work_root)
