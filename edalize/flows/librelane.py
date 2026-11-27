# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

from edalize.flows.generic import Generic


class Librelane(Generic):
    """Run the LibreLane RTL-to-GDSII flow to implement an ASIC"""

    argtypes = ["vlogdefine", "vlogparam"]

    @classmethod
    def get_flow_options(cls):
        return {k: v for k, v in cls.FLOW_OPTIONS.items() if k != "tool"}

    @classmethod
    def get_tool_options(cls, flow_options):
        flow = flow_options.get("frontends", []).copy() + ["librelane"]

        return cls.get_filtered_tool_options(flow, cls.FLOW_DEFINED_TOOL_OPTIONS)

    def configure_flow(self, flow_options):
        self.flow_options["tool"] = "librelane"
        return super().configure_flow(flow_options)
