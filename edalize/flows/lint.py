# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import os

from edalize.flows.generic import Generic

class Lint(Generic):
    """Run a simulation"""

    argtypes = ["plusarg", "vlogdefine", "vlogparam"]

    FLOW_OPTIONS = {
        **Generic.FLOW_OPTIONS,
        **{
        },
    }
