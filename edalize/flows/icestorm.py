# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import os.path
from importlib import import_module

from edalize.flows.edaflow import Edaflow


class Icestorm(Edaflow):
    """Open source toolchain for Lattice iCE40 FPGAs. Uses yosys for synthesis and nextpnr for Place & Route"""

    argtypes = ["vlogdefine", "vlogparam"]

    FLOW_DEFINED_TOOL_OPTIONS = {
        "yosys": {"arch": "ice40", "output_format": "json"},
        "nextpnr": {"arch": "ice40"},
    }

    FLOW_OPTIONS = {
        "frontends": {
            "type": "str",
            "desc": "Tools to run before yosys (e.g. sv2v)",
            "list": True,
        },
        "pnr": {
            "type": "str",
            "desc": "Select Place & Route tool. Legal values are *next* for nextpnr or *none* to only perform synthesis. Default is next",
        },
    }

    @classmethod
    def get_flow_options(cls):
        return cls.FLOW_OPTIONS.copy()

    @classmethod
    def get_tool_options(cls, flow_options):
        flow = flow_options.get("frontends", [])
        flow += ["yosys"]
        pnr = flow_options.get("pnr", "next")
        if pnr == "next":
            flow += ["nextpnr", "icepack", "icetime"]

        return cls.get_filtered_tool_options(flow, cls.FLOW_DEFINED_TOOL_OPTIONS)

    def extract_flow_options(self):
        return {
            k: v
            for (k, v) in self.edam.get("flow_options", {}).items()
            if k in self.get_flow_options()
        }

    def configure_flow(self, flow_options):
        name = self.edam["name"]
        # Check whether to run nextpnr or stop after synthesis
        # and set output from syntheis or pnr as default target depending
        # on value of pnr flow option
        pnr = flow_options.get("pnr", "next")
        if pnr == "next":
            flow = [
                ("yosys", ["nextpnr"], {"arch": "ice40", "output_format": "json"}),
                ("nextpnr", ["icepack", "icetime"], {"arch": "ice40"}),
                ("icepack", [], {}),
                ("icetime", [], {}),
            ]
            self.commands.set_default_target(name + ".bin")
        elif pnr == "none":
            flow = [("yosys", [], {"arch": "ice40", "output_format": "json"})]
            self.commands.set_default_target(name + ".json")
        else:
            raise RuntimeError(
                "Invalid pnr option '{}'. Valid values are 'next' for nextpnr or 'none' to only perform synthesis".format(
                    pnr
                )
            )

        # Add any user-specified frontends to the flow
        next_tool = "yosys"

        for frontend in reversed(flow_options.get("frontends", [])):
            flow[0:0] = [(frontend, [next_tool], {})]
            next_tool = frontend

        return flow

    def configure_tools(self, nodes):
        super().configure_tools(nodes)

        name = self.edam["name"]
        # Slot in statistics command which doesn't have an EdaTool class
        depends = name + ".asc"
        targets = name + ".stat"
        command = ["icebox_stat", depends, targets]
        self.commands.add(command, [targets], [depends])
        self.commands.add([], ["stats"], [targets])
