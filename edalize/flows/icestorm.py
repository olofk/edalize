# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import os.path
from importlib import import_module

from edalize.flows.edaflow import Edaflow, FlowGraph


class Icestorm(Edaflow):
    """Open source toolchain for Lattice iCE40 FPGAs. Uses yosys for synthesis and nextpnr for Place & Route"""

    argtypes = ["vlogdefine", "vlogparam"]

    _flow = {
        "yosys": {"fdto": {"arch": "ice40", "output_format": "json"}},
        "nextpnr": {"deps": ["yosys"], "fdto": {"arch": "ice40"}},
        "icepack": {"deps": ["nextpnr"]},
        "icetime": {"deps": ["nextpnr"]},
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
    def get_tool_options(cls, flow_options):
        tools = flow_options.get("frontends", []) + list(cls._flow)

        flow_defined_tool_options = {}
        for k, v in cls._flow.items():
            flow_defined_tool_options[k] = v.get("fdto", {})
        return cls.get_filtered_tool_options(tools, flow_defined_tool_options)

    def configure_flow(self, flow_options):

        flow = self._flow.copy()

        # Add any user-specified frontends to the flow
        deps = []
        for frontend in flow_options.get("frontends", []):
            flow[frontend] = {"deps": deps}
            deps = [frontend]

        flow["yosys"]["deps"] = deps

        # Check whether to run nextpnr or stop after synthesis
        # and set output from syntheis or pnr as default target depending
        # on value of pnr flow option
        name = self.edam["name"]
        self.commands.add([], ["synth"], [name + ".json"])
        self.commands.add([], ["bitstream"], [name + ".bin"])
        self.commands.set_default_target("bitstream")

        pnr = flow_options.get("pnr", "next")
        if pnr == "next":
            self.goal = "bitstream"
        elif pnr == "none":
            self.goal = "synth"
        else:
            raise RuntimeError(
                "Invalid pnr option '{}'. Valid values are 'next' for nextpnr or 'none' to only perform synthesis".format(
                    pnr
                )
            )

        return FlowGraph.fromdict(flow)

    def configure_tools(self, nodes):
        super().configure_tools(nodes)

        name = self.edam["name"]
        # Slot in statistics command which doesn't have an EdaTool class
        depends = name + ".asc"
        targets = name + ".stat"
        command = ["icebox_stat", depends, targets]
        self.commands.add(command, [targets], [depends])
        self.commands.add([], ["stats"], [targets])

    def build(self):
        self._run_tool("make", [self.goal], cwd=self.work_root)
