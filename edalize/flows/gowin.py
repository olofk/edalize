# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

from __future__ import annotations

from typing import Any

from edalize.flows.edaflow import FlowGraph
from edalize.flows.generic import Generic


class Gowin(Generic):
    """Official Gowin FPGA toolchain"""

    argtypes: list[str] = []

    @classmethod
    def get_flow_options(cls) -> dict[str, dict[str, Any]]:
        return {k: v for k, v in cls.FLOW_OPTIONS.items() if k != "tool"}

    @classmethod
    def get_tool_options(cls, flow_options: dict[str, Any]) -> dict[str, Any]:
        flow = flow_options.get("frontends", []).copy() + ["gowin"]

        return cls.get_filtered_tool_options(flow, cls.FLOW_DEFINED_TOOL_OPTIONS)

    def configure_flow(self, flow_options: dict[str, Any]) -> FlowGraph:
        self.flow_options["tool"] = "gowin"
        return super().configure_flow(flow_options)
