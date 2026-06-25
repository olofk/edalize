# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

from __future__ import annotations

from typing import Any

from edalize.flows.generic import Generic


class Lint(Generic):
    """Run a linter tool on the design"""

    argtypes = ["vlogdefine", "vlogparam"]

    FLOW_DEFINED_TOOL_OPTIONS: dict[str, dict[str, Any]] = {
        "verilator": {"mode": "lint-only", "exe": "false", "make_options": []},
        # verible, spyglass, ascentlint, slang...
    }
