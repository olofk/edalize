# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import os.path

from edalize.flows.edaflow import Edaflow


class Icestorm(Edaflow):
    """Open source toolchain for Lattice iCE40 FPGAs. Uses yosys for synthesis and nextpnr for Place & Route"""

    argtypes = ["vlogdefine", "vlogparam"]

    FLOW = [
        ("yosys", ["nextpnr"], {"arch": "ice40", "output_format": "json"}),
        ("nextpnr", ["icepack", "icetime"], {"arch": "ice40"}),
        ("icepack", [], {}),
        ("icetime", [], {}),
        #        ('icebox_stat', [], {}),
    ]

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

    def build_tool_graph(self):
        # FIXME: This makes an assumption that the first tool in self.FLOW is
        # a single entry point to the flow
        next_tool = self.FLOW[0][0]

        for frontend in reversed(self.flow_options.get("frontends", [])):
            self.FLOW[0:0] = [(frontend, [next_tool], {})]
            next_tool = frontend
        return super().build_tool_graph()

    def configure_tools(self, nodes):
        super().configure_tools(nodes)

        # Set output from syntheis or pnr as default target depending on
        # value of pnr flow option
        name = self.edam["name"]
        pnr = self.flow_options.get("pnr", "next")
        if pnr == "next":
            self.commands.set_default_target(name + ".bin")
        elif pnr == "none":
            self.commands.set_default_target(name + ".json")
        else:
            raise RuntimeError(
                "Invalid pnr option '{}'. Valid values are 'next' for nextpnr or 'none' to only perform synthesis".format(
                    pnr
                )
            )

        # Slot in statistics command which doesn't have an EdaTool class
        depends = name + ".asc"
        targets = name + ".stat"
        command = ["icebox_stat", depends, targets]
        self.commands.add(command, [targets], [depends])
        self.commands.add([], ["stats"], [targets])
