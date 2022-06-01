# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import os.path

from edalize.flows.edaflow import Edaflow

class F4PGA(Edaflow):
    """Free and open-source 'flow for FPGA's'. Uses Yosys for synthesys and VPR or NextPNR for place and route."""

    FLOW = [
        ("yosys", [""], {"arch":"", "output_format":"json"}),
        ("", [""], {"arch":""}),
        ("", [""], {}),
        ("", [], {})
    ]

    FLOW_OPTIONS = {}